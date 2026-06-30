"""Logical-id tokens for authored claims and concepts.

A logical id is a ``namespace:value`` pair that names an authored artifact
independently of its derived canonical ``ps:`` identity. These helpers normalise
namespace/value tokens to a stable character set so the same authored handle
always derives the same canonical artifact id.
"""

from __future__ import annotations

import re

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


def format_logical_id(namespace: object, value: object) -> str | None:
    """Return ``namespace:value`` for a logical-id pair, or ``None`` if invalid."""

    if not isinstance(namespace, str) or not isinstance(value, str):
        return None
    if not namespace or not value:
        return None
    return f"{namespace}:{value}"
