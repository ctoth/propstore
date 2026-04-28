"""Standards-based URI helpers for propstore entities and source bytes."""

from __future__ import annotations

import base64
import hashlib
import hmac
from pathlib import Path

from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

DEFAULT_URI_AUTHORITY = parse_tagging_authority("local@propstore,2026")
NI_SHA256_PREFIX = "ni:///sha-256;"


def normalize_uri_token(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "item"


def tag_uri(authority: str | TaggingAuthority, kind: str, specific: str) -> str:
    parsed_authority = parse_tagging_authority(authority)
    normalized_kind = normalize_uri_token(kind)
    normalized_specific = normalize_uri_token(specific)
    return f"tag:{parsed_authority}:{normalized_kind}/{normalized_specific}"


def source_tag_uri(
    name: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    return tag_uri(authority, "source", name)


def concept_tag_uri(
    name: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    return tag_uri(authority, "concept", name)


def claim_tag_uri(
    source_name: str,
    local_handle: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    parsed_authority = parse_tagging_authority(authority)
    source_token = normalize_uri_token(source_name)
    handle_token = normalize_uri_token(local_handle)
    return f"tag:{parsed_authority}:claim/{source_token}:{handle_token}"


def compute_ni_uri(payload: bytes, *, algorithm: str = "sha-256") -> str:
    if algorithm != "sha-256":
        raise ValueError("propstore only emits sha-256 ni URIs")
    digest = hashlib.sha256(payload).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{NI_SHA256_PREFIX}{encoded}"


def verify_ni_uri(uri: str, payload: bytes) -> bool:
    return hmac.compare_digest(uri, compute_ni_uri(payload))


def ni_uri_for_bytes(payload: bytes) -> str:
    return compute_ni_uri(payload)


def ni_uri_for_file(path: Path) -> str:
    return ni_uri_for_bytes(path.read_bytes())
