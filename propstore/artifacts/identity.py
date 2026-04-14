from __future__ import annotations

from copy import deepcopy
from typing import Any

from propstore.identity import (
    compute_claim_version_id,
    compute_concept_version_id,
    derive_concept_artifact_id,
    format_logical_id,
    normalize_identity_namespace,
    normalize_logical_value,
)


def normalize_canonical_claim_payload(
    data: dict[str, Any],
    *,
    strip_source_local: bool = False,
) -> dict[str, Any]:
    normalized = deepcopy(data)
    if strip_source_local:
        for field in ("id", "source_local_id", "artifact_code"):
            normalized.pop(field, None)
    normalized["version_id"] = compute_claim_version_id(normalized)
    return normalized


def normalize_canonical_concept_payload(
    data: dict[str, Any],
    *,
    canonical_name: str | None = None,
    domain: str | None = None,
    default_domain: str | None = None,
    local_handle: str | None = None,
    default_status: str | None = None,
    default_definition: str | None = None,
    default_form: str | None = None,
) -> dict[str, Any]:
    normalized = deepcopy(data)
    raw_id = normalized.pop("id", None)
    effective_name = canonical_name or normalized.get("canonical_name")
    if not isinstance(effective_name, str) or not effective_name:
        effective_name = str(raw_id or local_handle or "concept")
    normalized["canonical_name"] = effective_name

    effective_domain = domain
    if effective_domain is None:
        effective_domain = normalized.get("domain") or default_domain or "propstore"
    normalized["domain"] = effective_domain
    if default_status is not None and not isinstance(normalized.get("status"), str):
        normalized["status"] = default_status
    if default_definition is not None and not isinstance(normalized.get("definition"), str):
        normalized["definition"] = default_definition
    if default_form is not None and not isinstance(normalized.get("form"), str):
        normalized["form"] = default_form

    propstore_handle = normalize_logical_value(
        local_handle or _concept_local_handle(normalized, fallback=str(raw_id or effective_name))
    )
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = derive_concept_artifact_id("propstore", propstore_handle)
    normalized["artifact_id"] = artifact_id
    normalized["logical_ids"] = _concept_logical_ids(
        domain=str(effective_domain),
        canonical_name=str(effective_name),
        local_handle=propstore_handle,
        existing=normalized.get("logical_ids"),
    )
    normalized["version_id"] = compute_concept_version_id(normalized)
    return normalized


def concept_reference_keys(data: dict[str, Any], *, raw_id: str | None = None) -> set[str]:
    reference_keys: set[str] = set()

    def add(candidate: object) -> None:
        if isinstance(candidate, str) and candidate:
            reference_keys.add(candidate)

    add(data.get("artifact_id"))
    add(data.get("canonical_name"))
    if raw_id is not None:
        add(raw_id)
    for entry in data.get("logical_ids", []) or []:
        if not isinstance(entry, dict):
            continue
        add(entry.get("value"))
        formatted = format_logical_id(entry)
        if formatted is not None:
            reference_keys.add(formatted)
    for alias in data.get("aliases", []) or []:
        if isinstance(alias, dict):
            add(alias.get("name"))
    return reference_keys


def _concept_local_handle(data: dict[str, Any], *, fallback: str | None = None) -> str:
    logical_ids = data.get("logical_ids")
    if isinstance(logical_ids, list):
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if namespace == "propstore" and isinstance(value, str) and value:
                return normalize_logical_value(value)
    raw_id = data.get("id")
    if isinstance(raw_id, str) and raw_id:
        return normalize_logical_value(raw_id)
    return normalize_logical_value(fallback or data.get("canonical_name") or "concept")


def _concept_logical_ids(
    *,
    domain: str,
    canonical_name: str,
    local_handle: str,
    existing: object = None,
) -> list[dict[str, str]]:
    primary = {
        "namespace": normalize_identity_namespace(domain or "propstore"),
        "value": normalize_logical_value(canonical_name),
    }
    logical_ids = [primary]
    seen = {format_logical_id(primary)}
    if isinstance(existing, list):
        for entry in existing:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if not isinstance(namespace, str) or not isinstance(value, str):
                continue
            normalized = {
                "namespace": normalize_identity_namespace(namespace),
                "value": normalize_logical_value(value),
            }
            formatted = format_logical_id(normalized)
            if formatted is None or formatted in seen:
                continue
            if normalized["namespace"] == primary["namespace"]:
                continue
            logical_ids.append(normalized)
            seen.add(formatted)
    propstore_entry = {"namespace": "propstore", "value": normalize_logical_value(local_handle)}
    formatted_propstore = format_logical_id(propstore_entry)
    if formatted_propstore is not None and formatted_propstore not in seen:
        logical_ids.append(propstore_entry)
    return logical_ids
