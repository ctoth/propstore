from __future__ import annotations

import pytest

from quire.references import AmbiguousReferenceError, FamilyReferenceIndex

from propstore.families.claims.documents import ClaimDocument, ClaimLogicalIdDocument, ClaimSourceDocument
from propstore.families.contexts.documents import ContextDocument
from propstore.families.contexts.documents import ContextReferenceDocument
from propstore.families.registry import ClaimRef, ContextRef, SourceRef
from propstore.repository import Repository
from propstore.core.claim_types import ClaimType
from propstore.families.documents.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.families.documents.sources import SourceProvenanceDocument
from propstore.source.common import source_branch_name
from propstore.source.reference_indexes import (
    ImportedClaimHandle,
    imported_claim_handle_index,
    primary_claim_index,
    resolve_source_or_primary_claim_id,
    source_claim_index,
)


def test_source_claim_index_reads_source_claim_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.create_branch(source_branch_name("paper"))

    repo.families.source_claims.save(
        SourceRef("paper"),
        SourceClaimsDocument(
            source=ClaimSourceDocument(paper="paper"),
            claims=(
                SourceClaimDocument(
                    id="claim_a",
                    source_local_id="claim_a",
                    artifact_id="ps:claim:a",
                    logical_ids=(ClaimLogicalIdDocument(namespace="paper", value="claim_a"),),
                    type=ClaimType.OBSERVATION,
                    statement="A",
                    provenance=SourceProvenanceDocument(paper="paper", page=1),
                ),
            ),
        ),
        message="Write source claims",
    )

    index = source_claim_index(repo, "paper")

    assert index.require_id("claim_a") == "ps:claim:a"
    assert index.require_id("paper:claim_a") == "ps:claim:a"
    assert index.ids() == ("ps:claim:a",)


def test_primary_claim_index_reads_canonical_claim_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    repo.families.contexts.save(
        ContextRef("ctx_test"),
        ContextDocument(id="ctx_test", name="Test context"),
        message="Write context",
    )
    repo.families.claims.save(
        ClaimRef("ps:claim:a"),
        ClaimDocument(
            source=ClaimSourceDocument(paper="paper"),
            context=ContextReferenceDocument(id="ctx_test"),
            artifact_id="ps:claim:a",
            logical_ids=(ClaimLogicalIdDocument(namespace="paper", value="claim_a"),),
            type=ClaimType.OBSERVATION,
            statement="A",
            provenance=SourceProvenanceDocument(paper="paper", page=1),
        ),
        message="Write canonical claims",
    )

    index = primary_claim_index(repo)

    assert index.require_id("ps:claim:a") == "ps:claim:a"
    assert index.require_id("paper:claim_a") == "ps:claim:a"
    assert index.ids() == ("ps:claim:a",)


def test_source_before_primary_resolution_and_imported_ambiguity_are_quire_indexed() -> None:
    source_index = FamilyReferenceIndex.from_records(
        (
            ImportedClaimHandle("local", "ps:claim:local"),
            ImportedClaimHandle("paper:logical", "ps:claim:logical"),
        ),
        family="source_claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(lambda handle: (handle.handle,),),
    )
    canonical_index = FamilyReferenceIndex.from_records(
        (ImportedClaimHandle("master:logical", "ps:claim:master"),),
        family="claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(lambda handle: (handle.handle,),),
    )

    assert resolve_source_or_primary_claim_id(
        "local",
        source=source_index,
        primary=canonical_index,
    ) == "ps:claim:local"
    assert resolve_source_or_primary_claim_id(
        "paper:logical",
        source=source_index,
        primary=canonical_index,
    ) == "ps:claim:logical"
    assert resolve_source_or_primary_claim_id(
        "master:logical",
        source=source_index,
        primary=canonical_index,
    ) == "ps:claim:master"
    assert resolve_source_or_primary_claim_id(
        "ps:claim:master",
        source=source_index,
        primary=canonical_index,
    ) == "ps:claim:master"
    assert resolve_source_or_primary_claim_id(
        "missing",
        source=source_index,
        primary=canonical_index,
    ) is None

    with pytest.raises(AmbiguousReferenceError, match="dup"):
        imported_claim_handle_index(
            (
                ImportedClaimHandle("dup", "ps:claim:a"),
                ImportedClaimHandle("dup", "ps:claim:b"),
            )
        )
