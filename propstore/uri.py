"""Standards-based URI helpers for propstore entities and source bytes."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path


DEFAULT_URI_AUTHORITY = "local@propstore,2026"


def normalize_uri_token(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "item"


def tag_uri(authority: str, kind: str, specific: str) -> str:
    normalized_kind = normalize_uri_token(kind)
    normalized_specific = normalize_uri_token(specific)
    return f"tag:{authority}:{normalized_kind}/{normalized_specific}"


def source_tag_uri(name: str, *, authority: str = DEFAULT_URI_AUTHORITY) -> str:
    return tag_uri(authority, "source", name)


def concept_tag_uri(name: str, *, authority: str = DEFAULT_URI_AUTHORITY) -> str:
    return tag_uri(authority, "concept", name)


def claim_tag_uri(source_name: str, local_handle: str, *, authority: str = DEFAULT_URI_AUTHORITY) -> str:
    source_token = normalize_uri_token(source_name)
    handle_token = normalize_uri_token(local_handle)
    return f"tag:{authority}:claim/{source_token}:{handle_token}"


def ni_uri_for_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"ni:///sha-256;{encoded}"


def ni_uri_for_file(path: Path) -> str:
    return ni_uri_for_bytes(path.read_bytes())
