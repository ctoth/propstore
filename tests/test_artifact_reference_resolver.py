from __future__ import annotations

import pytest

from quire.references import AmbiguousReferenceError, FamilyReferenceIndex

from propstore.families.claims.declaration import ClaimDocument, ClaimLogicalIdDocument, ClaimSourceDocument
from propstore.families.contexts.declaration import ContextDocument
from propstore.families.contexts.declaration import ContextReferenceDocument
from propstore.families.registry import ClaimRef, ContextRef, SourceRef
from propstore.repository import Repository
from propstore.families.claims.types import ClaimType
from propstore.families.claims.references import (
    ImportedClaimReference,
    imported_claim_reference_index,
    resolve_first_claim_reference_id,
)
from propstore.families.claims.declaration import (
    SourceClaimDocument,
    SourceProvenanceDocument,
)
from propstore.source.reference_indexes import (
    primary_claim_index,
    source_claim_index,
)


def test_source_claim_index_reads_source_claim_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    branch = repo.families.source_claims.address(SourceRef("paper")).branch
    repo.git.create_branch(branch)

    repo.families.source_claims.save(
        SourceRef("paper"),
        (
            SourceClaimDocument(
                source=ClaimSourceDocument(paper="paper"),
                id="claim_a",
                source_local_id="claim_a",
                artifact_id="ps:claim:a",
                logical_ids=(ClaimLogicalIdDocument(namespace="paper", value="claim_a"),),
                type=ClaimType.OBSERVATION,
                statement="A",
                provenance=SourceProvenanceDocument(paper="paper", page=1),
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
            ImportedClaimReference("local", "ps:claim:local"),
            ImportedClaimReference("paper:logical", "ps:claim:logical"),
        ),
        family="source_claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(lambda handle: (handle.handle,),),
    )
    canonical_index = FamilyReferenceIndex.from_records(
        (ImportedClaimReference("master:logical", "ps:claim:master"),),
        family="claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(lambda handle: (handle.handle,),),
    )

    assert resolve_first_claim_reference_id(
        "local",
        source_index,
        canonical_index,
    ) == "ps:claim:local"
    assert resolve_first_claim_reference_id(
        "paper:logical",
        source_index,
        canonical_index,
    ) == "ps:claim:logical"
    assert resolve_first_claim_reference_id(
        "master:logical",
        source_index,
        canonical_index,
    ) == "ps:claim:master"
    assert resolve_first_claim_reference_id(
        "ps:claim:master",
        source_index,
        canonical_index,
    ) == "ps:claim:master"
    assert resolve_first_claim_reference_id(
        "missing",
        source_index,
        canonical_index,
    ) is None

    with pytest.raises(AmbiguousReferenceError, match="dup"):
        imported_claim_reference_index(
            (
                ImportedClaimReference("dup", "ps:claim:a"),
                ImportedClaimReference("dup", "ps:claim:b"),
            )
        )
