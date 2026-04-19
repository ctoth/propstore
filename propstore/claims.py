"""Typed claim document loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeAlias

from quire.artifacts import ArtifactHandle
from propstore.families.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.families.registry import ClaimsFileRef
from quire.documents import (
    convert_document_value,
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimsFileDocument]
ClaimFileEntry: TypeAlias = (
    LoadedClaimsFile | ArtifactHandle[Any, ClaimsFileRef, ClaimsFileDocument]
)


def load_claim_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    return load_document(
        path,
        ClaimsFileDocument,
        knowledge_root=knowledge_root,
    )


def loaded_claim_file_from_payload(
    *,
    filename: str,
    source_path: KnowledgePath | Path | None,
    data: dict[str, Any],
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    label = filename if source_path is None else str(source_path)
    return LoadedDocument(
        filename=filename,
        source_path=source_path,
        knowledge_root=knowledge_root,
        document=convert_document_value(
            data,
            ClaimsFileDocument,
            source=label,
        ),
    )


def claim_file_filename(claim_file: ClaimFileEntry) -> str:
    filename = getattr(claim_file, "filename", None)
    if isinstance(filename, str):
        return filename
    ref = getattr(claim_file, "ref", None)
    name = getattr(ref, "name", None)
    if isinstance(name, str):
        return name
    raise TypeError("claim file entry has no filename or ref name")


def claim_file_claims(claim_file: ClaimFileEntry) -> tuple[ClaimDocument, ...]:
    return claim_file.document.claims


def claim_file_source_paper(claim_file: ClaimFileEntry) -> str:
    return claim_file.document.source.paper


def claim_file_stage(claim_file: ClaimFileEntry) -> str | None:
    return claim_file.document.stage


def claim_file_payload(claim_file: ClaimFileEntry) -> dict[str, Any]:
    return claim_file.document.to_payload()
