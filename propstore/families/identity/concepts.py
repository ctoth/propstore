from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from quire.hashing import canonical_json_sha256

from propstore.families.identity import logical_ids

CONCEPT_VERSION_ID_EXCLUDED_FIELDS = ("artifact_id", "version_id", "id")
DEFAULT_CONCEPT_DOMAIN = "propstore"
DEFAULT_CONCEPT_NAME = "concept"
DEFAULT_LEXICAL_LANGUAGE = "en"
PARAMETERIZATION_RELATIONSHIPS_FIELD = "parameterization_relationships"
CONCEPT_SORTED_DICT_LIST_FIELDS = (
    "aliases",
    "relationships",
    PARAMETERIZATION_RELATIONSHIPS_FIELD,
)


def derive_concept_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic concept artifact ID from a logical handle."""
    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:concept:{digest}"


def canonicalize_concept_for_version(concept: dict[str, Any]) -> dict[str, Any]:
    """Normalize a concept into deterministic canonical content for hashing."""
    canonical = copy.deepcopy(concept)
    _drop_fields(canonical, CONCEPT_VERSION_ID_EXCLUDED_FIELDS)

    if isinstance(canonical.get("logical_ids"), list):
        canonical["logical_ids"] = _canonical_logical_ids(canonical.get("logical_ids"))

    for field in CONCEPT_SORTED_DICT_LIST_FIELDS:
        value = canonical.get(field)
        if isinstance(value, list):
            canonical[field] = _sorted_dicts(value)

    return canonical


def concept_version_payload_json(concept: dict[str, Any]) -> str:
    """Serialize canonical concept content for version hashing."""
    return json.dumps(
        canonicalize_concept_for_version(concept),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_concept_version_id(concept: dict[str, Any]) -> str:
    """Compute the immutable version identifier for a concept payload."""
    return canonical_json_sha256(canonicalize_concept_for_version(concept))


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
    normalized = copy.deepcopy(data)
    raw_id = normalized.pop("id", None)
    effective_name = _effective_concept_name(
        normalized,
        canonical_name=canonical_name,
        raw_id=raw_id,
        local_handle=local_handle,
    )
    effective_domain = _effective_concept_domain(
        normalized,
        domain=domain,
        default_domain=default_domain,
    )
    definition = _pop_effective_string(
        normalized,
        "definition",
        default_value=default_definition,
    )
    dimension_form = _pop_effective_string(
        normalized,
        "form",
        default_value=default_form,
    )
    if default_status is not None and not isinstance(normalized.get("status"), str):
        normalized["status"] = default_status

    propstore_handle = logical_ids.normalize_logical_value(
        local_handle
        or _concept_local_handle(normalized, fallback=str(raw_id or effective_name))
    )
    artifact_id = _concept_artifact_id(normalized, propstore_handle)
    normalized["artifact_id"] = artifact_id
    normalized["logical_ids"] = _concept_logical_ids(
        domain=effective_domain,
        canonical_name=effective_name,
        local_handle=propstore_handle,
        existing=normalized.get("logical_ids"),
    )
    ontology_reference = _ensure_ontology_reference(
        normalized,
        artifact_id=artifact_id,
        label=effective_name,
    )
    _ensure_lexical_entry(
        normalized,
        propstore_handle=propstore_handle,
        effective_name=effective_name,
        ontology_reference=ontology_reference,
        definition=definition,
        dimension_form=dimension_form,
    )
    _normalize_numeric_range(normalized)
    normalized["version_id"] = compute_concept_version_id(normalized)
    return normalized


def concept_reference_keys(data: dict[str, Any], *, raw_id: str | None = None) -> set[str]:
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


def _drop_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        payload.pop(field, None)


def _canonical_logical_ids(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized_handles: list[dict[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        namespace = entry.get("namespace")
        logical_value = entry.get("value")
        if isinstance(namespace, str) and isinstance(logical_value, str):
            normalized_handles.append({
                "namespace": namespace,
                "value": logical_value,
            })
    return sorted(normalized_handles, key=lambda item: (item["namespace"], item["value"]))


def _sorted_dicts(value: list[object]) -> list[dict[str, Any]]:
    return sorted(
        (item for item in value if isinstance(item, dict)),
        key=_canonical_json_sort_key,
    )


def _canonical_json_sort_key(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


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


def _ensure_lexical_entry(
    data: dict[str, Any],
    *,
    propstore_handle: str,
    effective_name: str,
    ontology_reference: dict[str, Any],
    definition: object,
    dimension_form: object,
) -> None:
    if isinstance(data.get("lexical_entry"), dict):
        return
    lexical_payload: dict[str, Any] = {
        "identifier": f"entry:{propstore_handle}",
        "canonical_form": {
            "written_rep": effective_name,
            "language": DEFAULT_LEXICAL_LANGUAGE,
        },
        "senses": [
            {
                "reference": ontology_reference,
                "usage": definition if isinstance(definition, str) else None,
            }
        ],
    }
    if isinstance(dimension_form, str):
        lexical_payload["physical_dimension_form"] = dimension_form
    data["lexical_entry"] = lexical_payload


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
