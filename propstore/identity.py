"""Identity helpers for first-class propstore objects."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

# Re-export ``LogicalId`` so external callers can import it from the
# top-level identity surface alongside the other identity helpers.
# The dataclass itself lives in ``propstore.core.id_types`` to keep the
# core types module dependency-free; this re-export is purely a public
# API convenience.
from propstore.core.id_types import LogicalId

__all__ = ["LogicalId"]


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


def normalize_claim_file_payload(
    data: dict[str, Any],
    *,
    default_namespace: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Normalize a claim-file payload onto the claim identity contract."""
    normalized_data = dict(data)
    source = normalized_data.get("source")
    raw_namespace = (
        source.get("paper")
        if isinstance(source, dict) and isinstance(source.get("paper"), str)
        else (default_namespace or "source")
    )
    namespace = normalize_identity_namespace(raw_namespace)

    raw_claims = list(normalized_data.get("claims", []))
    local_to_artifact: dict[str, str] = {}
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
            local_to_artifact[raw_id] = artifact_id
        local_to_artifact[primary_value] = artifact_id
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
                if isinstance(target, str) and target in local_to_artifact:
                    rewritten["target"] = local_to_artifact[target]
                rewritten_stances.append(rewritten)
            normalized["stances"] = rewritten_stances
        normalized["version_id"] = compute_claim_version_id(normalized)
        normalized_claims[index] = normalized

    normalized_data["claims"] = normalized_claims
    return normalized_data, local_to_artifact


def rewrite_stance_file_payload(
    data: dict[str, Any],
    *,
    local_to_artifact: dict[str, str],
) -> dict[str, Any]:
    """Rewrite a stance-file payload from local claim handles to artifact IDs."""
    normalized = dict(data)
    source_claim = normalized.get("source_claim")
    if isinstance(source_claim, str) and source_claim in local_to_artifact:
        normalized["source_claim"] = local_to_artifact[source_claim]

    raw_stances = normalized.get("stances")
    if not isinstance(raw_stances, list):
        return normalized

    rewritten_stances = []
    for stance in raw_stances:
        if not isinstance(stance, dict):
            rewritten_stances.append(stance)
            continue
        rewritten = dict(stance)
        target = rewritten.get("target")
        if isinstance(target, str) and target in local_to_artifact:
            rewritten["target"] = local_to_artifact[target]
        rewritten_stances.append(rewritten)
    normalized["stances"] = rewritten_stances
    return normalized


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
