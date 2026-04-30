from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from quire.hashing import canonical_json_sha256

from propstore.families.identity import logical_ids

CLAIM_VERSION_ID_EXCLUDED_FIELDS = ("artifact_id", "version_id", "id", "source_local_id")
CLAIM_SOURCE_LOCAL_FIELDS = ("id", "source_local_id", "artifact_code")
DEFAULT_CLAIM_NAMESPACE = "source"
DEFAULT_CLAIM_HANDLE_PREFIX = "claim"


def derive_claim_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic claim artifact ID from a logical handle."""
    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:claim:{digest}"


def canonicalize_claim_for_version(claim: dict[str, Any]) -> dict[str, Any]:
    """Normalize a claim into deterministic canonical content for hashing."""
    canonical = copy.deepcopy(claim)
    _drop_fields(canonical, CLAIM_VERSION_ID_EXCLUDED_FIELDS)

    if isinstance(canonical.get("logical_ids"), list):
        canonical["logical_ids"] = _canonical_logical_ids(canonical.get("logical_ids"))

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
            key=lambda stance: json.dumps(
                stance,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
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
    return canonical_json_sha256(canonicalize_claim_for_version(claim))


def normalize_claim_file_payload(
    data: dict[str, Any],
    *,
    default_namespace: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    normalized_data = dict(data)
    namespace = _claim_file_namespace(normalized_data, default_namespace)

    raw_claims = list(normalized_data.get("claims", []))
    local_handle_map: dict[str, str] = {}
    normalized_claims: list[Any] = []
    for index, claim in enumerate(raw_claims, start=1):
        normalized, local_handles = _normalize_claim_file_entry(claim, index, namespace)
        local_handle_map.update(local_handles)
        normalized_claims.append(normalized)

    for index, normalized in enumerate(normalized_claims):
        if not isinstance(normalized, dict):
            continue
        _rewrite_stance_targets(normalized, local_handle_map)
        _stamp_claim_version_id(normalized)
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
        _drop_fields(normalized, CLAIM_SOURCE_LOCAL_FIELDS)
    normalized["version_id"] = compute_claim_version_id(normalized)
    return normalized


def _drop_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        payload.pop(field, None)


def _claim_file_namespace(data: dict[str, Any], default_namespace: str | None) -> str:
    source = data.get("source")
    raw_namespace = (
        source.get("paper")
        if isinstance(source, dict) and isinstance(source.get("paper"), str)
        else (default_namespace or DEFAULT_CLAIM_NAMESPACE)
    )
    return logical_ids.normalize_identity_namespace(
        raw_namespace if isinstance(raw_namespace, str) else str(raw_namespace)
    )


def _normalize_claim_file_entry(
    claim: object,
    index: int,
    default_namespace: str,
) -> tuple[object, dict[str, str]]:
    if not isinstance(claim, dict):
        return claim, {}

    normalized = dict(claim)
    raw_id = normalized.pop("id", None)
    normalized["logical_ids"] = _normalize_claim_logical_ids(
        normalized.get("logical_ids"),
        raw_id=raw_id,
        index=index,
        default_namespace=default_namespace,
    )

    primary_namespace, primary_value = _primary_logical_handle(normalized["logical_ids"])
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = derive_claim_artifact_id(primary_namespace, primary_value)
        normalized["artifact_id"] = artifact_id

    local_handles = {primary_value: artifact_id}
    if isinstance(raw_id, str) and raw_id:
        local_handles[raw_id] = artifact_id
    return normalized, local_handles


def _normalize_claim_logical_ids(
    value: object,
    *,
    raw_id: object,
    index: int,
    default_namespace: str,
) -> list[dict[str, str]]:
    if isinstance(value, list) and value:
        normalized = _normalize_existing_logical_ids(value)
        if normalized:
            return normalized
    return [
        {
            "namespace": default_namespace,
            "value": _fallback_logical_value(raw_id, index),
        }
    ]


def _normalize_existing_logical_ids(value: list[object]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        namespace = entry.get("namespace")
        logical_value = entry.get("value")
        if not isinstance(namespace, str) or not isinstance(logical_value, str):
            continue
        normalized.append(
            {
                "namespace": logical_ids.normalize_identity_namespace(namespace),
                "value": logical_ids.normalize_logical_value(logical_value),
            }
        )
    return normalized


def _fallback_logical_value(raw_id: object, index: int) -> str:
    return logical_ids.normalize_logical_value(
        str(raw_id or f"{DEFAULT_CLAIM_HANDLE_PREFIX}{index}")
    )


def _primary_logical_handle(entries: list[dict[str, str]]) -> tuple[str, str]:
    first = entries[0]
    return str(first["namespace"]), str(first["value"])


def _rewrite_stance_targets(claim: dict[str, Any], local_handle_map: dict[str, str]) -> None:
    stances = claim.get("stances")
    if not isinstance(stances, list):
        return

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
    claim["stances"] = rewritten_stances


def _stamp_claim_version_id(claim: dict[str, Any]) -> None:
    claim["version_id"] = compute_claim_version_id(claim)


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
