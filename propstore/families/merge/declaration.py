"""Merge manifest charter and generated document type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId


MERGE_MANIFEST_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


class MergeManifestWitnessDocument(msgspec.Struct, forbid_unknown_fields=True):
    source_artifact_id: str
    source_paper: str | None = None
    source_page: int | None = None
    branch_origin: str | None = None
    rule_chain: tuple[str, ...] = ()


class MergeManifestArgumentDocument(msgspec.Struct, forbid_unknown_fields=True):
    assertion_id: str
    artifact_id: str
    logical_id: str
    canonical_claim_id: str | None = None
    branch_origins: tuple[str, ...] = ()
    witness_basis: tuple[MergeManifestWitnessDocument, ...] = ()
    materialized: bool = False


class MergeSemanticCandidateArgumentDocument(msgspec.Struct, forbid_unknown_fields=True):
    assertion_id: str
    logical_id: str
    artifact_id: str
    branch_origins: tuple[str, ...] = ()
    source_paper: str | None = None


class MergeSemanticCandidateDetailDocument(msgspec.Struct, forbid_unknown_fields=True):
    assertion_ids: tuple[str, ...] = ()
    logical_ids: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    arguments: tuple[MergeSemanticCandidateArgumentDocument, ...] = ()


class MergeManifestPayloadDocument(msgspec.Struct, forbid_unknown_fields=True):
    branch_a: str
    branch_b: str
    arguments: tuple[MergeManifestArgumentDocument, ...] = ()
    semantic_candidates: tuple[tuple[str, ...], ...] = ()
    semantic_candidate_details: tuple[MergeSemanticCandidateDetailDocument, ...] = ()


class MergeManifest(FamilyModel):
    pass


class _MergeManifestCharter(FamilyCharter):
    def generated_document(self, state: str | None = None) -> type[msgspec.Struct]:
        cached = self._generated_document_cache.get(state)
        if cached is not None:
            return cached

        document_type = msgspec.defstruct(
            "MergeManifestDocument",
            [("merge", MergeManifestPayloadDocument)],
            module=__name__,
            forbid_unknown_fields=True,
        )
        self._generated_document_cache[state] = document_type
        return document_type


MERGE_MANIFEST_CHARTER: FamilyCharter = _MergeManifestCharter(
    family=FamilyDefinition(
        key="merge_manifest",
        name="merge_manifest",
        contract_version=MERGE_MANIFEST_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-merge_manifest",
            contract_version=MERGE_MANIFEST_FAMILY_CONTRACT_VERSION,
            doc_type=MergeManifest,
            placement=FlatYamlPlacement(".derived/merge_manifest", str),
        ),
        identity_field="id",
    ),
    model=MergeManifest,
    fields=(
        CharterField(
            "id",
            str,
            primary_key=True,
            nullable=False,
            default="merge_manifest",
            default_sql="'merge_manifest'",
            document=False,
        ),
        CharterField("branch_a", str, nullable=False, document=False),
        CharterField("branch_b", str, nullable=False, document=False),
        CharterField(
            "arguments",
            tuple[MergeManifestArgumentDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            document=False,
        ),
        CharterField(
            "semantic_candidates",
            tuple[tuple[str, ...], ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            document=False,
        ),
        CharterField(
            "semantic_candidate_details",
            tuple[MergeSemanticCandidateDetailDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            document=False,
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

MERGE_MANIFEST_CHARTERS: tuple[FamilyCharter, ...] = (MERGE_MANIFEST_CHARTER,)

if TYPE_CHECKING:

    class MergeManifestDocument(msgspec.Struct, forbid_unknown_fields=True):
        merge: MergeManifestPayloadDocument

else:
    MergeManifestDocument: Any = MERGE_MANIFEST_CHARTER.generated_document()
    MergeManifestDocument.__name__ = "MergeManifestDocument"
    MergeManifestDocument.__qualname__ = "MergeManifestDocument"
    MergeManifestDocument.__module__ = __name__
