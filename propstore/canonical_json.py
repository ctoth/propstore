"""Strict canonical JSON encoding for content-addressed payloads."""

from __future__ import annotations

import rfc8785

from propstore.json_types import JsonValue


class CanonicalEncodingError(TypeError):
    """Raised when a payload is not JSON-native canonical data."""


def canonical_dumps(payload: JsonValue) -> str:
    """Encode JSON-native payloads deterministically and fail on unknown values."""

    try:
        return rfc8785.dumps(payload).decode("utf-8")
    except rfc8785.CanonicalizationError as exc:
        raise CanonicalEncodingError(str(exc)) from exc
