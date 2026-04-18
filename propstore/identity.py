"""Identity helpers for first-class propstore objects."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any


CLAIM_ARTIFACT_ID_RE = re.compile(r"^ps:claim:[A-Za-z0-9][A-Za-z0-9._-]*$")
CLAIM_VERSION_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CONCEPT_ARTIFACT_ID_RE = re.compile(r"^ps:concept:[A-Za-z0-9][A-Za-z0-9._-]*$")
CONCEPT_VERSION_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LOGICAL_NAMESPACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LOGICAL_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

_LOGICAL_CLAIM_ID_RE = re.compile(
    r"^(?P<namespace>[A-Za-z0-9][A-Za-z0-9._-]*):(?P<value>[A-Za-z0-9][A-Za-z0-9._/-]*)$"
)


def parse_claim_id(cid: str) -> tuple[str | None, str]:
    """Split a logical claim ID into ``(namespace, local_id)``."""
    match = _LOGICAL_CLAIM_ID_RE.match(cid)
    if match is None:
        return None, cid
    return match.group("namespace"), match.group("value")


def normalize_identity_namespace(value: str) -> str:
    """Return a valid logical-id namespace token."""
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    normalized = normalized.strip("._-")
    if not normalized:
        return "source"
    if not normalized[0].isalnum():
        normalized = f"ns_{normalized}"
    return normalized


def normalize_logical_value(value: str) -> str:
    """Return a valid logical-id value token."""
    normalized = re.sub(r"[^A-Za-z0-9._/-]+", "_", value.strip())
    normalized = normalized.strip("._/-")
    if not normalized:
        return "item"
    if not normalized[0].isalnum():
        normalized = f"id_{normalized}"
    return normalized


def derive_claim_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic claim artifact ID from a logical handle."""
    normalized_namespace = normalize_identity_namespace(namespace)
    normalized_value = normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()[:16]
    return f"ps:claim:{digest}"


def derive_concept_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic concept artifact ID from a logical handle."""
    normalized_namespace = normalize_identity_namespace(namespace)
    normalized_value = normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()[:16]
    return f"ps:concept:{digest}"


def format_logical_id(entry: dict[str, Any]) -> str | None:
    """Return ``namespace:value`` for a logical-id entry."""
    namespace = entry.get("namespace")
    value = entry.get("value")
    if not isinstance(namespace, str) or not isinstance(value, str):
        return None
    if not namespace or not value:
        return None
    return f"{namespace}:{value}"


def primary_logical_id(claim: dict[str, Any]) -> str | None:
    """Return the primary user-facing logical ID for a claim."""
    logical_ids = claim.get("logical_ids")
    if not isinstance(logical_ids, list) or not logical_ids:
        return None
    first = logical_ids[0]
    if not isinstance(first, dict):
        return None
    return format_logical_id(first)


def canonicalize_claim_for_version(claim: dict[str, Any]) -> dict[str, Any]:
    """Normalize a claim into deterministic canonical content for hashing."""
    canonical = copy.deepcopy(claim)
    canonical.pop("artifact_id", None)
    canonical.pop("version_id", None)
    canonical.pop("id", None)
    canonical.pop("source_local_id", None)

    logical_ids = canonical.get("logical_ids")
    if isinstance(logical_ids, list):
        normalized_handles: list[dict[str, str]] = []
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and isinstance(value, str):
                normalized_handles.append({
                    "namespace": namespace,
                    "value": value,
                })
        canonical["logical_ids"] = sorted(
            normalized_handles,
            key=lambda item: (item["namespace"], item["value"]),
        )

    conditions = canonical.get("conditions")
    if isinstance(conditions, list):
        canonical["conditions"] = sorted(
            condition for condition in conditions if isinstance(condition, str)
        )

    stances = canonical.get("stances")
    if isinstance(stances, list):
        normalized_stances = [stance for stance in stances if isinstance(stance, dict)]
        canonical["stances"] = sorted(
            normalized_stances,
            key=lambda stance: json.dumps(stance, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        )

    return canonical


def canonicalize_concept_for_version(concept: dict[str, Any]) -> dict[str, Any]:
    """Normalize a concept into deterministic canonical content for hashing."""
    canonical = copy.deepcopy(concept)
    canonical.pop("artifact_id", None)
    canonical.pop("version_id", None)
    canonical.pop("id", None)

    logical_ids = canonical.get("logical_ids")
    if isinstance(logical_ids, list):
        normalized_handles: list[dict[str, str]] = []
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and isinstance(value, str):
                normalized_handles.append({
                    "namespace": namespace,
                    "value": value,
                })
        canonical["logical_ids"] = sorted(
            normalized_handles,
            key=lambda item: (item["namespace"], item["value"]),
        )

    aliases = canonical.get("aliases")
    if isinstance(aliases, list):
        normalized_aliases = [alias for alias in aliases if isinstance(alias, dict)]
        canonical["aliases"] = sorted(
            normalized_aliases,
            key=lambda alias: json.dumps(alias, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        )

    relationships = canonical.get("relationships")
    if isinstance(relationships, list):
        normalized_relationships = [rel for rel in relationships if isinstance(rel, dict)]
        canonical["relationships"] = sorted(
            normalized_relationships,
            key=lambda rel: json.dumps(rel, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        )

    parameterizations = canonical.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        normalized_parameterizations = [param for param in parameterizations if isinstance(param, dict)]
        canonical["parameterization_relationships"] = sorted(
            normalized_parameterizations,
            key=lambda param: json.dumps(param, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        )

    return canonical


def claim_version_payload_json(claim: dict[str, Any]) -> str:
    """Serialize canonical claim content for version hashing."""
    canonical = canonicalize_claim_for_version(claim)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_claim_version_id(claim: dict[str, Any]) -> str:
    """Compute the immutable version identifier for a claim payload."""
    payload = claim_version_payload_json(claim)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def concept_version_payload_json(concept: dict[str, Any]) -> str:
    """Serialize canonical concept content for version hashing."""
    canonical = canonicalize_concept_for_version(concept)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_concept_version_id(concept: dict[str, Any]) -> str:
    """Compute the immutable version identifier for a concept payload."""
    payload = concept_version_payload_json(concept)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def normalize_claim_file_payload(
    data: dict[str, Any],
    *,
    default_namespace: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    normalized_data = dict(data)
    source = normalized_data.get("source")
    raw_namespace = (
        source.get("paper")
        if isinstance(source, dict) and isinstance(source.get("paper"), str)
        else (default_namespace or "source")
    )
    namespace = normalize_identity_namespace(raw_namespace if isinstance(raw_namespace, str) else str(raw_namespace))

    raw_claims = list(normalized_data.get("claims", []))
    local_handle_map: dict[str, str] = {}
    normalized_claims: list[Any] = []
    for index, claim in enumerate(raw_claims, start=1):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue

        normalized = dict(claim)
        raw_id = normalized.pop("id", None)
        artifact_id = normalized.get("artifact_id")
        logical_ids = normalized.get("logical_ids")

        if not isinstance(logical_ids, list) or not logical_ids:
            logical_value = normalize_logical_value(str(raw_id or f"claim{index}"))
            normalized["logical_ids"] = [{"namespace": namespace, "value": logical_value}]
        else:
            cleaned_logical_ids: list[dict[str, str]] = []
            for entry in logical_ids:
                if not isinstance(entry, dict):
                    continue
                entry_namespace = entry.get("namespace")
                entry_value = entry.get("value")
                if not isinstance(entry_namespace, str) or not isinstance(entry_value, str):
                    continue
                cleaned_logical_ids.append(
                    {
                        "namespace": normalize_identity_namespace(entry_namespace),
                        "value": normalize_logical_value(entry_value),
                    }
                )
            if not cleaned_logical_ids:
                logical_value = normalize_logical_value(str(raw_id or f"claim{index}"))
                cleaned_logical_ids = [{"namespace": namespace, "value": logical_value}]
            normalized["logical_ids"] = cleaned_logical_ids

        primary_entry = normalized["logical_ids"][0]
        primary_namespace = str(primary_entry["namespace"])
        primary_value = str(primary_entry["value"])
        if not isinstance(artifact_id, str) or not artifact_id:
            artifact_id = derive_claim_artifact_id(primary_namespace, primary_value)
            normalized["artifact_id"] = artifact_id

        if isinstance(raw_id, str) and raw_id:
            local_handle_map[raw_id] = artifact_id
        local_handle_map[primary_value] = artifact_id
        normalized_claims.append(normalized)

    for index, normalized in enumerate(normalized_claims):
        if not isinstance(normalized, dict):
            continue
        stances = normalized.get("stances")
        if isinstance(stances, list):
            rewritten_stances = []
            for stance in stances:
                if not isinstance(stance, dict):
                    rewritten_stances.append(stance)
                    continue
                rewritten = dict(stance)
                target = rewritten.get("target")
                if isinstance(target, str) and target in local_handle_map:
                    rewritten["target"] = local_handle_map[target]
                rewritten_stances.append(rewritten)
            normalized["stances"] = rewritten_stances
        normalized["version_id"] = compute_claim_version_id(normalized)
        normalized_claims[index] = normalized

    normalized_data["claims"] = normalized_claims
    return normalized_data, local_handle_map


def normalize_canonical_claim_payload(
    data: dict[str, Any],
    *,
    strip_source_local: bool = False,
) -> dict[str, Any]:
    normalized = copy.deepcopy(data)
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
    normalized = copy.deepcopy(data)
    raw_id = normalized.pop("id", None)
    lexical_entry = normalized.get("lexical_entry")
    lexical_name: object = None
    if isinstance(lexical_entry, dict):
        canonical_form = lexical_entry.get("canonical_form")
        if isinstance(canonical_form, dict):
            lexical_name = canonical_form.get("written_rep")
    effective_name = canonical_name or normalized.pop("canonical_name", None) or lexical_name
    if not isinstance(effective_name, str) or not effective_name:
        effective_name = str(raw_id or local_handle or "concept")

    effective_domain = domain
    if effective_domain is None:
        effective_domain = (
            normalized.pop("domain", None)
            or default_domain
            or _primary_logical_namespace(normalized.get("logical_ids"))
            or "propstore"
        )
    else:
        normalized.pop("domain", None)
    if default_status is not None and not isinstance(normalized.get("status"), str):
        normalized["status"] = default_status
    definition = normalized.pop("definition", None)
    if default_definition is not None and not isinstance(definition, str):
        definition = default_definition
    dimension_form = normalized.pop("form", None)
    if default_form is not None and not isinstance(dimension_form, str):
        dimension_form = default_form

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
    ontology_reference = normalized.get("ontology_reference")
    if not isinstance(ontology_reference, dict):
        ontology_reference = {
            "uri": artifact_id,
            "label": str(effective_name),
        }
        normalized["ontology_reference"] = ontology_reference
    if not isinstance(normalized.get("lexical_entry"), dict):
        lexical_payload: dict[str, Any] = {
            "identifier": f"entry:{propstore_handle}",
            "canonical_form": {
                "written_rep": str(effective_name),
                "language": "en",
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
        normalized["lexical_entry"] = lexical_payload
    range_value = normalized.get("range")
    if (
        isinstance(range_value, list)
        and len(range_value) == 2
        and all(isinstance(item, (int, float)) for item in range_value)
    ):
        normalized["range"] = [float(range_value[0]), float(range_value[1])]
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


def _primary_logical_namespace(logical_ids: object) -> str | None:
    if not isinstance(logical_ids, list) or not logical_ids:
        return None
    first = logical_ids[0]
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
