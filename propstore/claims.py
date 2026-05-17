"""Typed claim artifact loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeAlias

from quire.artifacts import ArtifactHandle
from propstore.families.batch_specs import CLAIM_BATCH_SPEC
from propstore.families.claims.documents import ClaimDocument
from propstore.families.registry import ClaimRef
from quire.documents import (
    convert_document_value,
    decode_document_batch_bytes,
    decode_yaml_mapping,
    encode_yaml_value,
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path
from quire.documents import LoadedDocument

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimDocument]
ClaimFileEntry: TypeAlias = (
    LoadedClaimsFile | ArtifactHandle[Any, ClaimRef, ClaimDocument]
)


def load_claim_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    return load_document(
        path,
        ClaimDocument,
        store_root=knowledge_root,
    )


def loaded_claim_file_from_payload(
    *,
    filename: str,
    source_path: KnowledgePath | Path | None,
    data: dict[str, Any],
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedClaimsFile:
    label = filename if source_path is None else str(source_path)
    claim_payload = data
    raw_claims = data.get("claims")
    if isinstance(raw_claims, list):
        claims = raw_claims
        if len(claims) != 1:
            raise ValueError("claim artifact payload must contain exactly one claim")
        claim_payload = dict(claims[0])
        source_payload = data.get("source")
        if isinstance(source_payload, dict) and "source" not in claim_payload:
            claim_payload["source"] = source_payload
    return LoadedDocument(
        filename=filename,
        artifact_path=source_path,
        store_root=knowledge_root,
        document=convert_document_value(
            claim_payload,
            ClaimDocument,
            source=label,
        ),
    )


def load_claim_batch_file(
    path: KnowledgePath | Path,
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> tuple[LoadedClaimsFile, ...]:
    artifact_path = coerce_tree_path(path)
    root_path = None if knowledge_root is None else coerce_tree_path(knowledge_root)
    data = decode_yaml_mapping(artifact_path.read_bytes(), source=artifact_path.as_posix())
    return claim_batch_files_from_payload(
        filename=artifact_path.stem,
        source_path=artifact_path,
        data=data,
        knowledge_root=root_path,
    )


def claim_batch_files_from_payload(
    *,
    filename: str,
    source_path: KnowledgePath | Path | None,
    data: dict[str, Any],
    knowledge_root: KnowledgePath | Path | None = None,
) -> tuple[LoadedClaimsFile, ...]:
    label = filename if source_path is None else str(source_path)
    stage = data.get("stage")
    batch_payload = dict(data)
    batch_payload.pop("stage", None)
    documents = decode_document_batch_bytes(
        encode_yaml_value(batch_payload),
        CLAIM_BATCH_SPEC,
        source=label,
    )

    loaded: list[LoadedClaimsFile] = []
    for index, document in enumerate(documents, start=1):
        claim_file = LoadedDocument(
            filename=f"{filename}#{index}",
            artifact_path=source_path,
            store_root=knowledge_root,
            document=document,
        )
        setattr(claim_file, "source_path", source_path)
        if isinstance(stage, str):
            setattr(claim_file, "stage", stage)
        loaded.append(claim_file)
    return tuple(loaded)


def claim_file_filename(claim_file: ClaimFileEntry) -> str:
    filename = getattr(claim_file, "filename", None)
    if isinstance(filename, str):
        return filename
    ref = getattr(claim_file, "ref", None)
    artifact_id = getattr(ref, "artifact_id", None)
    if isinstance(artifact_id, str):
        return artifact_id
    raise TypeError("claim artifact entry has no filename or artifact_id")


def claim_file_claims(claim_file: ClaimFileEntry) -> tuple[ClaimDocument, ...]:
    return (claim_file.document,)


def claim_file_source_paper(claim_file: ClaimFileEntry) -> str:
    source = claim_file.document.source
    if source is not None:
        return source.paper
    provenance = claim_file.document.provenance
    if provenance is not None and provenance.paper is not None:
        return provenance.paper
    return claim_file_filename(claim_file)


def claim_file_stage(claim_file: ClaimFileEntry) -> str | None:
    stage = getattr(claim_file, "stage", None)
    return stage if isinstance(stage, str) else None


def claim_file_payload(claim_file: ClaimFileEntry) -> dict[str, Any]:
    return claim_file.document.to_payload()
