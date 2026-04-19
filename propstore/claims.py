"""Typed claim document loading and semantic access helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias

from quire.artifacts import ArtifactHandle
from propstore.families.documents.claims import ClaimDocument, ClaimsFileDocument
from propstore.families.registry import ClaimsFileRef
from quire.documents import (
    convert_document_value,
    load_document,
)
from quire.tree_path import TreePath as KnowledgePath
from quire.documents import LoadedDocument

if TYPE_CHECKING:
    from propstore.repository import Repository

LoadedClaimsFile: TypeAlias = LoadedDocument[ClaimsFileDocument]
ClaimFileEntry: TypeAlias = (
    LoadedClaimsFile | ArtifactHandle[Any, ClaimsFileRef, ClaimsFileDocument]
)


class ClaimWorkflowError(Exception):
    """Base class for expected claim workflow failures."""


class UnknownClaimError(ClaimWorkflowError):
    def __init__(self, claim_id: str) -> None:
        super().__init__(f"Claim '{claim_id}' not found.")
        self.claim_id = claim_id


class ClaimComparisonError(ClaimWorkflowError):
    pass


class ClaimSidecarMissingError(ClaimWorkflowError):
    pass


class ClaimEmbeddingModelError(ClaimWorkflowError):
    pass


def _require_sidecar(repo: Repository) -> Path:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise ClaimSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return sidecar


def _required_int(result: Mapping[str, object], key: str) -> int:
    value = result[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ClaimWorkflowError(f"expected integer field '{key}'")
    return value


def _required_stances_by_claim(value: object) -> dict[str, list[dict[str, object]]]:
    if not isinstance(value, Mapping):
        raise ClaimWorkflowError("expected stances_by_claim mapping")
    stances_by_claim: dict[str, list[dict[str, object]]] = {}
    for claim_id, stances in value.items():
        if not isinstance(claim_id, str) or not isinstance(stances, list):
            raise ClaimWorkflowError(
                "expected stances_by_claim mapping of claim IDs to stance lists"
            )
        if not all(isinstance(stance, dict) for stance in stances):
            raise ClaimWorkflowError("expected stance entries to be mappings")
        stances_by_claim[claim_id] = stances
    return stances_by_claim


def _algorithm_variables(claim: Mapping[str, object]) -> dict[str, str]:
    variables_json = claim.get("variables_json")
    if not variables_json:
        return {}
    variables = json.loads(str(variables_json))
    if not isinstance(variables, list):
        raise ValueError("algorithm variables must be stored as a list of bindings")
    result: dict[str, str] = {}
    for variable in variables:
        if isinstance(variable, dict):
            name = variable.get("name") or variable.get("symbol")
            concept = variable.get("concept", "")
            if name:
                result[str(name)] = str(concept)
    return result


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
