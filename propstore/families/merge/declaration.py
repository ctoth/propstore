"""Merge manifest charter and generated document type."""

from __future__ import annotations

from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field, column
from quire.charters import FamilyCharter
from quire.versions import VersionId


MERGE_MANIFEST_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


class MergeManifestWitnessDocument(CharterDoc):
    source_artifact_id: str
    source_paper: str | None = None
    source_page: int | None = None
    branch_origin: str | None = None
    rule_chain: tuple[str, ...] = ()


class MergeManifestArgumentDocument(CharterDoc):
    assertion_id: str
    artifact_id: str
    logical_id: str
    canonical_claim_id: str | None = None
    branch_origins: tuple[str, ...] = ()
    witness_basis: tuple[MergeManifestWitnessDocument, ...] = ()
    materialized: bool = False


class MergeSemanticCandidateArgumentDocument(CharterDoc):
    assertion_id: str
    logical_id: str
    artifact_id: str
    branch_origins: tuple[str, ...] = ()
    source_paper: str | None = None


class MergeSemanticCandidateDetailDocument(CharterDoc):
    assertion_ids: tuple[str, ...] = ()
    logical_ids: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    arguments: tuple[MergeSemanticCandidateArgumentDocument, ...] = ()


class MergeManifestPayloadDocument(CharterDoc):
    branch_a: str
    branch_b: str
    arguments: tuple[MergeManifestArgumentDocument, ...] = ()
    semantic_candidates: tuple[tuple[str, ...], ...] = ()
    semantic_candidate_details: tuple[MergeSemanticCandidateDetailDocument, ...] = ()


@charter(
    key="merge_manifest",
    name="merge_manifest",
    contract_version=MERGE_MANIFEST_FAMILY_CONTRACT_VERSION,
    placement=".derived/merge_manifest",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-merge_manifest",
    model_name="MergeManifest",
    extra_columns=(
        column(
            "id",
            str,
            primary_key=True,
            nullable=False,
            default="merge_manifest",
            default_sql="'merge_manifest'",
        ),
        column("branch_a", str, nullable=False),
        column("branch_b", str, nullable=False),
        column(
            "arguments",
            tuple[MergeManifestArgumentDocument, ...],
            json=True,
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        column(
            "semantic_candidates",
            tuple[tuple[str, ...], ...],
            json=True,
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        column(
            "semantic_candidate_details",
            tuple[MergeSemanticCandidateDetailDocument, ...],
            json=True,
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
    ),
)
class MergeManifestDocument(CharterDoc):
    merge: Annotated[MergeManifestPayloadDocument, charter_field(document_only=True)]


MERGE_MANIFEST_CHARTER: FamilyCharter = MergeManifestDocument.__charter__

MERGE_MANIFEST_CHARTERS: tuple[FamilyCharter, ...] = (MERGE_MANIFEST_CHARTER,)
