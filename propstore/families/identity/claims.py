"""Deterministic identity for authored claims.

The canonical claim artifact id is ``ps:claim:<sha256 of namespace:value>`` —
derived from the claim's logical handle, not minted by storage. The version id
is ``sha256:<hex>`` over the claim's *content* with the identity/source-local
fields excluded, so re-authoring identical content yields the same version while
the immutable artifact id is provenance-free.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import TypeGuard

from quire.hashing import canonical_json_sha256

from propstore.families.identity import logical_ids

CLAIM_VERSION_ID_EXCLUDED_FIELDS = (
    "artifact_id",
    "version_id",
    "id",
    "source_local_id",
    "source",
)
CLAIM_SOURCE_LOCAL_FIELDS = ("id", "source_local_id", "artifact_code")


def derive_claim_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic claim artifact ID from a logical handle."""

    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:claim:{digest}"


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    """Narrow an arbitrary JSON value to a homogeneous ``list[object]``.

    The one TypeGuard the JSON-payload canonicalization needs: ``isinstance``
    on a bare ``list`` narrows to ``list[Unknown]``, which strict pyright
    rejects; this restores the element type as ``object`` without a cast.
    """

    return isinstance(value, list)


def _json_sort_key(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def canonicalize_claim_for_version(claim: dict[str, object]) -> dict[str, object]:
    """Normalize a claim into deterministic canonical content for hashing.

    Drops the identity/source-local fields, sorts the authored ``conditions``,
    and orders the ``logical_ids`` / ``stances`` lists by their canonical JSON so
    re-authoring identical content (in any list order) yields one version id.
    """

    canonical = copy.deepcopy(claim)
    for field in CLAIM_VERSION_ID_EXCLUDED_FIELDS:
        canonical.pop(field, None)

    raw_conditions = canonical.get("conditions")
    if _is_object_list(raw_conditions):
        canonical["conditions"] = sorted(
            value for value in raw_conditions if isinstance(value, str)
        )

    for list_field in ("logical_ids", "stances"):
        raw = canonical.get(list_field)
        if _is_object_list(raw):
            canonical[list_field] = sorted(raw, key=_json_sort_key)

    return canonical


def compute_claim_version_id(claim: dict[str, object]) -> str:
    """Compute the immutable ``sha256:`` version identifier for a claim payload."""

    return canonical_json_sha256(canonicalize_claim_for_version(claim))


def normalize_canonical_claim_payload(
    data: dict[str, object],
    *,
    strip_source_local: bool = False,
) -> dict[str, object]:
    """Return a copy of *data* with a freshly-stamped ``version_id``."""

    normalized = copy.deepcopy(data)
    if strip_source_local:
        for field in CLAIM_SOURCE_LOCAL_FIELDS:
            normalized.pop(field, None)
    normalized["version_id"] = compute_claim_version_id(normalized)
    return normalized
