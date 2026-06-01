"""Typed claim artifact loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from propstore.families.claims.declaration import CLAIM_BATCH_SPEC, ClaimDocument
from quire.documents import (
    convert_document_value,
    decode_document_batch_bytes,
    decode_yaml_mapping,
    document_to_payload,
    encode_yaml_value,
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path
from quire.documents import LoadedDocument


class LoadedClaimsFile(LoadedDocument[ClaimDocument]):
    """Loaded canonical claim document plus file-level claim metadata."""

    stage: str | None

    def __init__(
        self,
        *,
        filename: str,
        artifact_path: KnowledgePath | Path | None = None,
        store_root: KnowledgePath | Path | None = None,
        document: ClaimDocument,
        stage: str | None = None,
    ) -> None:
        super().__init__(
            filename=filename,
            artifact_path=artifact_path,
            store_root=store_root,
            document=document,
        )
        self.stage = stage


def load_claim_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    loaded = load_document(
        path,
        ClaimDocument,
        store_root=knowledge_root,
    )
    return LoadedClaimsFile(
        filename=loaded.filename,
        artifact_path=loaded.artifact_path,
        store_root=loaded.store_root,
        document=loaded.document,
    )


def load_claim_batch_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> tuple[LoadedClaimsFile, ...]:
    artifact_path = coerce_tree_path(path)
    root_path = None if knowledge_root is None else coerce_tree_path(knowledge_root)
    data = decode_yaml_mapping(
        artifact_path.read_bytes(), source=artifact_path.as_posix()
    )
    return claim_batch_files_from_payload(
        filename=artifact_path.name,
        source_path=artifact_path,
        data=data,
        knowledge_root=root_path,
    )


def claim_file_filename(claim_file: LoadedClaimsFile) -> str:
    return claim_file.filename


def claim_file_claims(claim_file: LoadedClaimsFile) -> tuple[ClaimDocument, ...]:
    return (claim_file.document,)


def claim_file_source_paper(claim_file: LoadedClaimsFile) -> str:
    source = claim_file.document.source
    if source is not None:
        return source.paper
    provenance = claim_file.document.provenance
    if provenance is not None and provenance.paper is not None:
        return provenance.paper
    return claim_file_filename(claim_file)


def claim_file_stage(claim_file: LoadedClaimsFile) -> str | None:
    return claim_file.stage
