"""Normalize semantic family writes during committed repository imports."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from quire.artifacts import ArtifactFamily
from quire.documents import decode_yaml_mapping
from quire.family_store import DocumentFamilyStore

from propstore.claim_references import ImportedClaimHandleIndex
from propstore.families.addresses import SemanticFamilyAddress
from propstore.families.registry import (
    PropstoreFamily,
    semantic_family_for_path,
    semantic_import_families,
)
from propstore.families.identity.claims import (
    normalize_canonical_claim_payload,
    normalize_claim_file_payload,
)
from propstore.families.identity.concepts import (
    concept_reference_keys,
    normalize_canonical_concept_payload,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class PlannedSemanticWrite:
    family: ArtifactFamily[Any, Any, Any]
    ref: object
    document: object
    relpath: SemanticFamilyAddress


@dataclass
class SemanticImportState:
    repository_name: str
    concept_ref_map: dict[str, str] = field(default_factory=dict)
    local_handle_index: ImportedClaimHandleIndex = field(default_factory=ImportedClaimHandleIndex)
    warnings: list[str] = field(default_factory=list)


SemanticImportBatch = Callable[
    [
        DocumentFamilyStore["Repository"],
        Sequence[str],
        Mapping[str, bytes],
        SemanticImportState,
    ],
    Mapping[str, PlannedSemanticWrite],
]


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    return decode_yaml_mapping(content, source=path)


def _planned_write(
    store: DocumentFamilyStore["Repository"],
    path: str,
    payload: object,
) -> PlannedSemanticWrite:
    family = semantic_family_for_path(path).artifact_family
    ref = store.ref_from_path(cast(Any, family), path)
    document = store.coerce(cast(Any, family), payload, source=path)
    address = store.address(cast(Any, family), ref)
    return PlannedSemanticWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=SemanticFamilyAddress(address.require_path()),
    )


def _document_payload(
    store: DocumentFamilyStore["Repository"],
    write: PlannedSemanticWrite,
) -> object:
    return store.payload(write.document, cast(Any, write.family))


def _claim_source_from_import_path(path: str) -> dict[str, str]:
    return {"paper": Path(path).stem}


def _rewrite_reference(value: Any, reference_map: Mapping[str, str]) -> Any:
    if not isinstance(value, str):
        return value
    return reference_map.get(value, value)


def _rewrite_concept_payload_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    if "replaced_by" in rewritten:
        rewritten["replaced_by"] = _rewrite_reference(rewritten.get("replaced_by"), concept_ref_map)

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        rewritten["relationships"] = [
            (
                {**relationship, "target": _rewrite_reference(relationship.get("target"), concept_ref_map)}
                if isinstance(relationship, dict)
                else relationship
            )
            for relationship in relationships
        ]

    parameterizations = rewritten.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        updated_parameterizations = []
        for parameterization in parameterizations:
            if not isinstance(parameterization, dict):
                updated_parameterizations.append(parameterization)
                continue
            copied = dict(parameterization)
            inputs = copied.get("inputs")
            if isinstance(inputs, list):
                copied["inputs"] = [_rewrite_reference(input_id, concept_ref_map) for input_id in inputs]
            updated_parameterizations.append(copied)
        rewritten["parameterization_relationships"] = updated_parameterizations

    return normalize_canonical_concept_payload(rewritten)


def _rewrite_claim_concept_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: Mapping[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    claims = rewritten.get("claims")
    if not isinstance(claims, list):
        return rewritten

    updated_claims: list[Any] = []
    for claim in claims:
        if not isinstance(claim, dict):
            updated_claims.append(claim)
            continue
        copied = dict(claim)
        if "concept" in copied:
            copied["concept"] = _rewrite_reference(copied.get("concept"), concept_ref_map)
        if "target_concept" in copied:
            copied["target_concept"] = _rewrite_reference(copied.get("target_concept"), concept_ref_map)
        concepts = copied.get("concepts")
        if isinstance(concepts, list):
            copied["concepts"] = [_rewrite_reference(concept_ref, concept_ref_map) for concept_ref in concepts]
        for field_name in ("variables", "parameters"):
            values = copied.get(field_name)
            if not isinstance(values, list):
                continue
            copied[field_name] = [
                (
                    {**value, "concept": _rewrite_reference(value.get("concept"), concept_ref_map)}
                    if isinstance(value, dict)
                    else value
                )
                for value in values
            ]
        updated_claims.append(normalize_canonical_claim_payload(copied))

    rewritten["claims"] = updated_claims
    return rewritten


def _normalize_concept_payload(
    data: dict[str, Any],
    *,
    default_domain: str,
) -> tuple[dict[str, Any], set[str]]:
    raw_id = data.get("id")
    normalized = normalize_canonical_concept_payload(
        dict(data),
        default_domain=str(default_domain or "propstore"),
    )
    return normalized, concept_reference_keys(
        normalized,
        raw_id=raw_id if isinstance(raw_id, str) else None,
    )


def _normalize_concept_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    seeded: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        canonical_name = payload.get("canonical_name")
        raw_id = payload.get("id")
        effective_name = canonical_name if isinstance(canonical_name, str) and canonical_name else str(raw_id or Path(path).stem or "concept")
        payload.setdefault("canonical_name", effective_name)
        payload.setdefault("status", "accepted")
        payload.setdefault("definition", effective_name)
        payload.setdefault("form", "structural")

        normalized_payload, reference_keys = _normalize_concept_payload(payload, default_domain=state.repository_name)
        concept_write = _planned_write(store, path, normalized_payload)
        seeded[path] = concept_write
        artifact_id = getattr(concept_write.document, "artifact_id", None)
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"Imported concept {path!r} is missing artifact_id after normalization")
        for reference_key in reference_keys:
            state.concept_ref_map[str(reference_key)] = artifact_id

    normalized: dict[str, PlannedSemanticWrite] = {}
    for path, concept_write in seeded.items():
        payload = _document_payload(store, concept_write)
        if not isinstance(payload, dict):
            raise TypeError(f"Imported concept {path!r} did not render to a mapping payload")
        normalized[path] = _planned_write(
            store,
            path,
            _rewrite_concept_payload_refs(payload, concept_ref_map=state.concept_ref_map),
        )
    return normalized


def _normalize_claim_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    for path in paths:
        payload = _decode_yaml(writes[path], path=path)
        source = payload.get("source")
        has_source = isinstance(source, dict) and isinstance(source.get("paper"), str) and bool(source.get("paper"))
        normalized_payload, local_map = normalize_claim_file_payload(payload, default_namespace=state.repository_name)
        if not has_source:
            normalized_payload["source"] = _claim_source_from_import_path(path)
        rewritten_payload = _rewrite_claim_concept_refs(normalized_payload, concept_ref_map=state.concept_ref_map)
        normalized[path] = _planned_write(store, path, rewritten_payload)
        for local_id, artifact_id in local_map.items():
            if state.local_handle_index.record(local_id, artifact_id):
                state.warnings.append(
                    f"ambiguous imported claim handle {local_id!r}; stance files must use artifact IDs"
                )
    return normalized


def _normalize_stance_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    return {
        path: _planned_write(
            store,
            path,
            state.local_handle_index.rewrite_stance_payload(_decode_yaml(writes[path], path=path), path=path),
        )
        for path in paths
    }


def _normalize_passthrough_batch(
    store: DocumentFamilyStore["Repository"],
    paths: Sequence[str],
    writes: Mapping[str, bytes],
    state: SemanticImportState,
) -> Mapping[str, PlannedSemanticWrite]:
    del state
    return {
        path: _planned_write(store, path, _decode_yaml(writes[path], path=path))
        for path in paths
    }


_SEMANTIC_IMPORT_NORMALIZERS: Mapping[PropstoreFamily, SemanticImportBatch] = {
    PropstoreFamily.CONCEPTS: _normalize_concept_batch,
    PropstoreFamily.CLAIMS: _normalize_claim_batch,
    PropstoreFamily.STANCES: _normalize_stance_batch,
}


def normalize_semantic_import_writes(
    store: DocumentFamilyStore["Repository"],
    writes: Mapping[str, bytes],
    *,
    repository_name: str,
) -> tuple[dict[str, PlannedSemanticWrite], list[str]]:
    normalized: dict[str, PlannedSemanticWrite] = {}
    state = SemanticImportState(repository_name=repository_name)
    for family in semantic_import_families():
        family_paths = [
            path
            for path in sorted(writes)
            if semantic_family_for_path(path).name == family.name
        ]
        if not family_paths:
            continue
        normalizer = _SEMANTIC_IMPORT_NORMALIZERS.get(cast(PropstoreFamily, family.key), _normalize_passthrough_batch)
        normalized.update(normalizer(store, family_paths, writes, state))
    return normalized, list(state.warnings)
