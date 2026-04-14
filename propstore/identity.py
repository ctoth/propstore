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
