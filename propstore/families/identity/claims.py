from __future__ import annotations

import hashlib
import re
from typing import Any

from propstore.families.identity import logical_ids

CLAIM_SOURCE_LOCAL_FIELDS = ("id", "source_local_id", "artifact_code")
DEFAULT_CLAIM_NAMESPACE = "source"
DEFAULT_CLAIM_HANDLE_PREFIX = "claim"
_RAW_CLAIM_LOCAL_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def derive_claim_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic claim artifact ID from a logical handle."""
    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:claim:{digest}"


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
    raw_id_valid = _raw_claim_id_is_valid(raw_id)
    if isinstance(raw_id, str) and not raw_id_valid:
        normalized["id"] = raw_id
    normalized["logical_ids"] = _normalize_claim_logical_ids(
        normalized.get("logical_ids"),
        raw_id=raw_id if raw_id_valid else None,
        index=index,
        default_namespace=default_namespace,
    )

    primary_namespace, primary_value = _primary_logical_handle(
        normalized["logical_ids"]
    )
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = derive_claim_artifact_id(primary_namespace, primary_value)
        normalized["artifact_id"] = artifact_id

    local_handles = {primary_value: artifact_id}
    if isinstance(raw_id, str) and raw_id_valid:
        local_handles[raw_id] = artifact_id
    return normalized, local_handles


def _raw_claim_id_is_valid(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    namespace, local_id = logical_ids.parse_claim_id(value)
    if namespace is not None and not logical_ids.LOGICAL_NAMESPACE_RE.match(namespace):
        return False
    return _RAW_CLAIM_LOCAL_ID_RE.match(local_id) is not None


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


def _rewrite_stance_targets(
    claim: dict[str, Any], local_handle_map: dict[str, str]
) -> None:
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
