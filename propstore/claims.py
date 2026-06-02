"""Typed claim artifact loading helpers."""

from __future__ import annotations

from pathlib import Path

from propstore.families.claims.declaration import ClaimDocument
from quire.documents import (
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument


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
