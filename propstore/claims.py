"""Typed claim document loading and semantic access helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeAlias

from propstore.artifacts.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.artifacts.schema import (
    convert_document_value,
    load_document,
    load_document_dir,
)
from propstore.knowledge_path import KnowledgePath
from propstore.loaded import LoadedDocument

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimsFileDocument]


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


def load_claim_files(claims_dir: KnowledgePath | Path | None) -> list[LoadedClaimsFile]:
    """Load all direct child claim YAML files from a claims subtree."""

    return load_document_dir(claims_dir, ClaimsFileDocument)


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


def claim_file_claims(claim_file: LoadedClaimsFile) -> tuple[ClaimDocument, ...]:
    return claim_file.document.claims


def claim_file_source_paper(claim_file: LoadedClaimsFile) -> str:
    return claim_file.document.source.paper


def claim_file_stage(claim_file: LoadedClaimsFile) -> str | None:
    return claim_file.document.stage


def claim_file_payload(claim_file: LoadedClaimsFile) -> dict[str, Any]:
    return claim_file.document.to_payload()
