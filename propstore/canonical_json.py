"""Strict canonical JSON encoding for content-addressed payloads."""

from __future__ import annotations

import json

from propstore.json_types import JsonValueT


class CanonicalEncodingError(TypeError):
    """Raised when a payload is not JSON-native canonical data."""


def canonical_dumps(payload: JsonValueT) -> str:
    """Encode JSON-native payloads deterministically and fail on unknown values."""

    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalEncodingError(str(exc)) from exc
