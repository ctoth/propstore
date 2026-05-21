"""Typed claim metadata access shared by claim analyzers."""

from __future__ import annotations

from typing import Any

from propstore.core.graph_types import ClaimNode
from propstore.families.claims.declaration import Claim


def claim_metadata_value(claim: Claim | ClaimNode, key: str) -> Any:
    if isinstance(claim, ClaimNode):
        if key in {"id", "claim_id", "artifact_id"}:
            return claim.claim_id
        value = getattr(claim, key, None)
        if value is not None:
            return value
        return _unfreeze_metadata_value(claim.attribute_value(key))

    if key in {"claim_id", "artifact_id"}:
        return claim.id
    value = getattr(claim, key, None)
    if value is not None:
        return value
    numeric_payload = getattr(claim, "numeric_payload", None)
    if numeric_payload is not None:
        value = getattr(numeric_payload, key, None)
        if value is not None:
            return value
    return None


def _unfreeze_metadata_value(value: Any) -> Any:
    if not isinstance(value, tuple):
        return value
    if all(
        isinstance(item, tuple)
        and len(item) == 2
        and isinstance(item[0], str)
        for item in value
    ):
        return {key: _unfreeze_metadata_value(item) for key, item in value}
    return tuple(_unfreeze_metadata_value(item) for item in value)
