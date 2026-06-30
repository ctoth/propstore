"""Standards-based URI helpers for propstore entities and source bytes.

propstore identifies concepts, sources, and claims with RFC 4151 ``tag:`` URIs
minted under a :class:`~propstore.uri_authority.TaggingAuthority`. A tag URI is a
stable, human-meaningful name that never depends on storage layout — the same
concept name under the same authority always yields the same URI, which is what
lets vocabulary reconciliation compare ontology references by identity (CLAUDE.md)
rather than by string tokens.

For byte-exact content identity propstore mints RFC 6920 ``ni`` URIs
(:func:`compute_ni_uri`), the SHA-256 hash carrier used by the provenance and
micropublication identity boundaries. Kuhn & Dumontier 2014 discuss ni-URIs as
related work (p. 4) and note the trusty-URI module identifier is lost in that form
(p. 7), so this is the ni-URI byte primitive, not a full trusty artifact code.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from pathlib import Path

from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

DEFAULT_URI_AUTHORITY = parse_tagging_authority("local@propstore,2026")
NI_SHA256_PREFIX = "ni:///sha-256;"


def normalize_uri_token(value: str) -> str:
    """Reduce ``value`` to a URI-safe token (alphanumerics, ``_-.``)."""

    cleaned = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in value.strip()
    )
    cleaned = cleaned.strip("._-")
    return cleaned or "item"


def tag_uri(authority: str | TaggingAuthority, kind: str, specific: str) -> str:
    """Mint an RFC 4151 ``tag:`` URI of the form ``tag:<authority>:<kind>/<specific>``."""

    parsed_authority = parse_tagging_authority(authority)
    normalized_kind = normalize_uri_token(kind)
    normalized_specific = normalize_uri_token(specific)
    return f"tag:{parsed_authority}:{normalized_kind}/{normalized_specific}"


def concept_tag_uri(
    name: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    """Return the canonical concept tag URI for ``name`` under ``authority``."""

    return tag_uri(authority, "concept", name)


def source_tag_uri(
    name: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    """Return the canonical source tag URI for ``name`` under ``authority``."""

    return tag_uri(authority, "source", name)


def claim_tag_uri(
    source_name: str,
    local_handle: str,
    *,
    authority: str | TaggingAuthority = DEFAULT_URI_AUTHORITY,
) -> str:
    """Return the canonical claim tag URI for a source-local claim handle."""

    parsed_authority = parse_tagging_authority(authority)
    source_token = normalize_uri_token(source_name)
    handle_token = normalize_uri_token(local_handle)
    return f"tag:{parsed_authority}:claim/{source_token}:{handle_token}"


def compute_ni_uri(payload: bytes, *, algorithm: str = "sha-256") -> str:
    """Return an RFC 6920 ``ni`` URI naming exactly ``payload``.

    Only SHA-256 is emitted: Kuhn & Dumontier 2014 give SHA-256 ni-URI examples
    (p. 4), and propstore's identity boundary is single-algorithm so an artifact
    code is comparable by string equality.
    """
    if algorithm != "sha-256":
        raise ValueError("propstore only emits sha-256 ni URIs")
    digest = hashlib.sha256(payload).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{NI_SHA256_PREFIX}{encoded}"


def verify_ni_uri(uri: str, payload: bytes) -> bool:
    """Verify that ``uri`` names exactly ``payload`` under :func:`compute_ni_uri`."""
    return hmac.compare_digest(uri, compute_ni_uri(payload))


def ni_uri_for_bytes(payload: bytes) -> str:
    """Return the ``ni`` URI for exact ``payload`` bytes."""
    return compute_ni_uri(payload)


def ni_uri_for_file(path: Path) -> str:
    """Return the ``ni`` URI for the exact bytes of the file at ``path``."""
    return ni_uri_for_bytes(path.read_bytes())
