from __future__ import annotations

from quire.documents import DocumentStruct


class MergeManifestArgumentDocument(DocumentStruct):
    assertion_id: str
    artifact_id: str
    logical_id: str
    canonical_claim_id: str | None = None
    branch_origins: tuple[str, ...] = ()
    materialized: bool = False


class MergeSemanticCandidateArgumentDocument(DocumentStruct):
    assertion_id: str
    logical_id: str
    artifact_id: str
    branch_origins: tuple[str, ...] = ()
    source_paper: str | None = None


class MergeSemanticCandidateDetailDocument(DocumentStruct):
    assertion_ids: tuple[str, ...] = ()
    logical_ids: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    arguments: tuple[MergeSemanticCandidateArgumentDocument, ...] = ()


class MergeManifestPayloadDocument(DocumentStruct):
    branch_a: str
    branch_b: str
    arguments: tuple[MergeManifestArgumentDocument, ...] = ()
    semantic_candidates: tuple[tuple[str, ...], ...] = ()
    semantic_candidate_details: tuple[MergeSemanticCandidateDetailDocument, ...] = ()


class MergeManifestDocument(DocumentStruct):
    merge: MergeManifestPayloadDocument
