from __future__ import annotations

import hashlib
from typing import Any

from propstore.families.identity import logical_ids

DEFAULT_CONCEPT_DOMAIN = "propstore"
DEFAULT_CONCEPT_NAME = "concept"
DEFAULT_LEXICAL_LANGUAGE = "en"


def derive_concept_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic concept artifact ID from a logical handle."""
    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:concept:{digest}"


def concept_reference_keys(
    data: dict[str, Any], *, raw_id: str | None = None
) -> set[str]:
    reference_keys: set[str] = set()
    _add_reference_key(reference_keys, data.get("artifact_id"))
    _add_reference_key(reference_keys, data.get("canonical_name"))
    if raw_id is not None:
        _add_reference_key(reference_keys, raw_id)

    for entry in data.get("logical_ids", []) or []:
        if not isinstance(entry, dict):
            continue
        _add_reference_key(reference_keys, entry.get("value"))
        formatted = logical_ids.format_logical_id(entry)
        if formatted is not None:
            reference_keys.add(formatted)

    for alias in data.get("aliases", []) or []:
        if isinstance(alias, dict):
            _add_reference_key(reference_keys, alias.get("name"))
    return reference_keys


def _effective_concept_name(
    data: dict[str, Any],
    *,
    canonical_name: str | None,
    raw_id: object,
    local_handle: str | None,
) -> str:
    lexical_name = _lexical_canonical_name(data.get("lexical_entry"))
    effective_name = canonical_name or data.pop("canonical_name", None) or lexical_name
    if isinstance(effective_name, str) and effective_name:
        return effective_name
    return str(raw_id or local_handle or DEFAULT_CONCEPT_NAME)


def _lexical_canonical_name(lexical_entry: object) -> object:
    if not isinstance(lexical_entry, dict):
        return None
    canonical_form = lexical_entry.get("canonical_form")
    if not isinstance(canonical_form, dict):
        return None
    return canonical_form.get("written_rep")


def _effective_concept_domain(
    data: dict[str, Any],
    *,
    domain: str | None,
    default_domain: str | None,
) -> str:
    if domain is not None:
        data.pop("domain", None)
        return str(domain)
    return str(
        data.pop("domain", None)
        or default_domain
        or _primary_logical_namespace(data.get("logical_ids"))
        or DEFAULT_CONCEPT_DOMAIN
    )


def _pop_effective_string(
    data: dict[str, Any],
    field: str,
    *,
    default_value: str | None,
) -> object:
    value = data.pop(field, None)
    if default_value is not None and not isinstance(value, str):
        return default_value
    return value


def _concept_artifact_id(data: dict[str, Any], propstore_handle: str) -> str:
    artifact_id = data.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return derive_concept_artifact_id(DEFAULT_CONCEPT_DOMAIN, propstore_handle)


def _ensure_ontology_reference(
    data: dict[str, Any],
    *,
    artifact_id: str,
    label: str,
) -> dict[str, Any]:
    ontology_reference = data.get("ontology_reference")
    if isinstance(ontology_reference, dict):
        return ontology_reference
    ontology_reference = {
        "uri": artifact_id,
        "label": label,
    }
    data["ontology_reference"] = ontology_reference
    return ontology_reference


def _normalize_numeric_range(data: dict[str, Any]) -> None:
    range_value = data.get("range")
    if (
        isinstance(range_value, list)
        and len(range_value) == 2
        and all(isinstance(item, (int, float)) for item in range_value)
    ):
        data["range"] = [float(range_value[0]), float(range_value[1])]


def _add_reference_key(reference_keys: set[str], candidate: object) -> None:
    if isinstance(candidate, str) and candidate:
        reference_keys.add(candidate)


def _concept_local_handle(data: dict[str, Any], *, fallback: str | None = None) -> str:
    logical_id_entries = data.get("logical_ids")
    if isinstance(logical_id_entries, list):
        for entry in logical_id_entries:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if namespace == DEFAULT_CONCEPT_DOMAIN and isinstance(value, str) and value:
                return logical_ids.normalize_logical_value(value)
    raw_id = data.get("id")
    if isinstance(raw_id, str) and raw_id:
        return logical_ids.normalize_logical_value(raw_id)
    return logical_ids.normalize_logical_value(
        fallback or data.get("canonical_name") or DEFAULT_CONCEPT_NAME
    )


def _primary_logical_namespace(logical_id_entries: object) -> str | None:
    if not isinstance(logical_id_entries, list) or not logical_id_entries:
        return None
    first = logical_id_entries[0]
    if not isinstance(first, dict):
        return None
    namespace = first.get("namespace")
    if not isinstance(namespace, str) or not namespace:
        return None
    return namespace


def _concept_logical_ids(
    *,
    domain: str,
    canonical_name: str,
    local_handle: str,
    existing: object = None,
) -> list[dict[str, str]]:
    primary = {
        "namespace": logical_ids.normalize_identity_namespace(
            domain or DEFAULT_CONCEPT_DOMAIN
        ),
        "value": logical_ids.normalize_logical_value(canonical_name),
    }
    logical_id_entries = [primary]
    seen = {logical_ids.format_logical_id(primary)}
    if isinstance(existing, list):
        for entry in existing:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if not isinstance(namespace, str) or not isinstance(value, str):
                continue
            normalized = {
                "namespace": logical_ids.normalize_identity_namespace(namespace),
                "value": logical_ids.normalize_logical_value(value),
            }
            formatted = logical_ids.format_logical_id(normalized)
            if formatted is None or formatted in seen:
                continue
            if normalized["namespace"] == primary["namespace"]:
                continue
            logical_id_entries.append(normalized)
            seen.add(formatted)
    propstore_entry = {
        "namespace": DEFAULT_CONCEPT_DOMAIN,
        "value": logical_ids.normalize_logical_value(local_handle),
    }
    formatted_propstore = logical_ids.format_logical_id(propstore_entry)
    if formatted_propstore is not None and formatted_propstore not in seen:
        logical_id_entries.append(propstore_entry)
    return logical_id_entries
