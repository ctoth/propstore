"""Deterministic identity for authored claims.

The canonical claim artifact id is ``ps:claim:<sha256 of namespace:value>`` —
derived from the claim's logical handle, not minted by storage. The version id
is ``sha256:<hex>`` over the claim's *content* with the identity/source-local
fields excluded, so re-authoring identical content yields the same version while
the immutable artifact id is provenance-free.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import msgspec
from quire.canonical import canonical_json_sha256

from propstore.families.identity import logical_ids

if TYPE_CHECKING:
    from propstore.families.sources import SourceClaimDocument

CLAIM_VERSION_ID_EXCLUDED_FIELDS = (
    "artifact_id",
    "version_id",
    "id",
    "source_local_id",
    "source",
)


def derive_claim_artifact_id(namespace: str, value: str) -> str:
    """Derive a deterministic claim artifact ID from a logical handle."""

    normalized_namespace = logical_ids.normalize_identity_namespace(namespace)
    normalized_value = logical_ids.normalize_logical_value(value)
    digest = hashlib.sha256(
        f"{normalized_namespace}:{normalized_value}".encode("utf-8")
    ).hexdigest()
    return f"ps:claim:{digest}"


def _encoded_sort_key(value: msgspec.Struct) -> bytes:
    return msgspec.json.encode(value)


def canonicalize_claim_for_version(
    claim: SourceClaimDocument,
) -> SourceClaimDocument:
    """Order one typed claim's unordered authored collections for hashing."""

    return msgspec.structs.replace(
        claim,
        conditions=tuple(sorted(claim.conditions)),
        logical_ids=tuple(sorted(claim.logical_ids, key=_encoded_sort_key)),
        stances=tuple(sorted(claim.stances, key=_encoded_sort_key)),
    )


def _version_payload(claim: SourceClaimDocument) -> dict[str, object]:
    payload = msgspec.json.decode(
        msgspec.json.encode(canonicalize_claim_for_version(claim)),
        type=dict[str, object],
    )
    for field in CLAIM_VERSION_ID_EXCLUDED_FIELDS:
        payload.pop(field, None)
    return payload


def compute_claim_version_id(claim: SourceClaimDocument) -> str:
    """Compute the immutable content version of one typed source claim."""

    return canonical_json_sha256(_version_payload(claim))


def stable_claim_logical_value(
    claim: SourceClaimDocument,
    *,
    source_uri: str,
) -> str:
    """Return the source-scoped stable logical value of one typed claim."""

    payload = msgspec.json.decode(
        msgspec.json.encode(canonicalize_claim_for_version(claim)),
        type=dict[str, object],
    )
    for field in ("id", "artifact_id", "version_id", "logical_ids", "source_local_id"):
        payload.pop(field, None)
    encoded = json.dumps(
        {"source_uri": source_uri, "claim": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"claim_{digest}"
