from __future__ import annotations

import pytest

from propstore.artifacts import (
    CLAIMS_FILE_FAMILY,
    SOURCE_CLAIMS_FAMILY,
    ClaimReferenceIndex,
    ClaimReferenceResolver,
    ClaimsFileRef,
    ImportedClaimHandleIndex,
    SourceRef,
    load_primary_branch_claim_reference_index,
    load_source_claim_reference_index,
)
from propstore.claim_documents import ClaimLogicalIdDocument, ClaimSourceDocument, ClaimsFileDocument
from propstore.cli.repository import Repository
from propstore.core.claim_types import ClaimType
from propstore.repo.branch import create_branch
from propstore.source_documents import SourceClaimDocument, SourceClaimsDocument
from propstore.source_documents import SourceProvenanceDocument
from propstore.source.common import source_branch_name


def test_load_source_claim_reference_index_reads_source_claim_artifacts(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    create_branch(repo.git, source_branch_name("paper"))

    repo.artifacts.save(
        SOURCE_CLAIMS_FAMILY,
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

    index = load_source_claim_reference_index(repo, "paper")

    assert index.local_to_artifact == {"claim_a": "ps:claim:a"}
    assert index.logical_to_artifact == {"paper:claim_a": "ps:claim:a"}
    assert index.artifact_ids == {"ps:claim:a"}


def test_load_primary_branch_claim_reference_index_reads_canonical_claim_files(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    repo.artifacts.save(
        CLAIMS_FILE_FAMILY,
        ClaimsFileRef("paper"),
        ClaimsFileDocument(
            source=ClaimSourceDocument(paper="paper"),
            claims=(
                SourceClaimDocument(
                    artifact_id="ps:claim:a",
                    logical_ids=(ClaimLogicalIdDocument(namespace="paper", value="claim_a"),),
                    type=ClaimType.OBSERVATION,
                    statement="A",
                    provenance=SourceProvenanceDocument(paper="paper", page=1),
                ),
            ),
        ),
        message="Write canonical claims",
    )

    index = load_primary_branch_claim_reference_index(repo)

    assert index.local_to_artifact == {}
    assert index.logical_to_artifact == {"paper:claim_a": "ps:claim:a"}
    assert index.artifact_ids == {"ps:claim:a"}


def test_claim_reference_resolver_and_imported_handle_index_behave_explicitly() -> None:
    resolver = ClaimReferenceResolver(
        source=ClaimReferenceIndex(
            local_to_artifact={"local": "ps:claim:local"},
            logical_to_artifact={"paper:logical": "ps:claim:logical"},
            artifact_ids={"ps:claim:local"},
        ),
        primary=ClaimReferenceIndex(
            logical_to_artifact={"master:logical": "ps:claim:master"},
            artifact_ids={"ps:claim:master"},
        ),
    )

    assert resolver.resolve_promoted_target("local") == "ps:claim:local"
    assert resolver.resolve_promoted_target("paper:logical") == "ps:claim:logical"
    assert resolver.resolve_promoted_target("master:logical") == "ps:claim:master"
    assert resolver.resolve_promoted_target("ps:claim:master") == "ps:claim:master"
    assert resolver.target_is_known("master:logical") is True
    assert resolver.target_is_known("missing") is False

    imported = ImportedClaimHandleIndex()
    assert imported.record("dup", "ps:claim:a") is False
    assert imported.record("dup", "ps:claim:b") is True
    with pytest.raises(ValueError, match="ambiguous target 'dup'"):
        imported.require_unambiguous("dup", path="stances/demo.yaml", role="target")
