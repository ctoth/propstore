"""Shared concept-side identity and resolution helpers for the sidecar."""

from __future__ import annotations

import hashlib

from propstore.families.identity.logical_ids import (
    format_logical_id,
    primary_logical_id,
)
from propstore.families.identity.concepts import compute_concept_version_id


def concept_content_hash(data: dict) -> str:
    version_id = data.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id.removeprefix("sha256:")
    h = hashlib.sha256()
    h.update((data.get("canonical_name", "")).encode())
    h.update((data.get("domain", "")).encode())
    h.update((data.get("definition", "")).encode())
    return h.hexdigest()


def concept_logical_ids(concept: dict) -> list[dict[str, str]]:
    logical_ids = concept.get("logical_ids")
    if isinstance(logical_ids, list):
        normalized: list[dict[str, str]] = []
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and namespace and isinstance(value, str) and value:
                normalized.append({"namespace": namespace, "value": value})
        if normalized:
            return normalized
    return []


def concept_primary_logical_id(concept: dict) -> str | None:
    primary = primary_logical_id(concept)
    if isinstance(primary, str) and primary:
        return primary
    logical_ids = concept_logical_ids(concept)
    if logical_ids:
        return format_logical_id(logical_ids[0])
    return None


def concept_artifact_id(concept: dict) -> str | None:
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return None


def concept_version_id(concept: dict) -> str | None:
    version_id = concept.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id
    if concept_artifact_id(concept) is None:
        return None
    logical_ids = concept_logical_ids(concept)
    if not logical_ids:
        return None
    canonical = dict(concept)
    canonical["artifact_id"] = concept_artifact_id(concept)
    canonical["logical_ids"] = logical_ids
    return compute_concept_version_id(canonical)


def concept_reference_candidates(concept: dict) -> set[str]:
    candidates: set[str] = set()
    raw_id = concept.get("id")
    if isinstance(raw_id, str) and raw_id:
        candidates.add(raw_id)
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        candidates.add(artifact_id)
    canonical_name = concept.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        candidates.add(canonical_name)
    for logical_id in concept.get("logical_ids", []) or []:
        if not isinstance(logical_id, dict):
            continue
        formatted = format_logical_id(logical_id)
        if formatted:
            candidates.add(formatted)
        value = logical_id.get("value")
        if isinstance(value, str) and value:
            candidates.add(value)
    for alias in concept.get("aliases", []) or []:
        if not isinstance(alias, dict):
            continue
        alias_name = alias.get("name")
        if isinstance(alias_name, str) and alias_name:
            candidates.add(alias_name)
    return candidates


def resolve_concept_reference(
    concept_ref: str | None,
    concept_registry: dict,
) -> str | None:
    if not concept_ref:
        return concept_ref

    direct = concept_registry.get(concept_ref)
    if isinstance(direct, dict):
        resolved = direct.get("_storage_id") or direct.get("artifact_id") or direct.get("id")
        if resolved:
            return resolved

    seen_ids: set[str] = set()
    for concept in concept_registry.values():
        if not isinstance(concept, dict):
            continue
        concept_id = concept.get("_storage_id") or concept.get("artifact_id") or concept.get("id")
        if not concept_id or concept_id in seen_ids:
            continue
        seen_ids.add(concept_id)
        if concept_ref in concept_reference_candidates(concept):
            return concept_id

    return concept_ref
