"""Standards-based URI helpers for propstore entities.

propstore identifies concepts (and, in later phases, sources and claims) with
RFC 4151 ``tag:`` URIs minted under a :class:`~propstore.uri_authority.TaggingAuthority`.
A tag URI is a stable, human-meaningful name that never depends on storage layout
— the same concept name under the same authority always yields the same URI, which
is what lets vocabulary reconciliation compare ontology references by identity
(CLAUDE.md) rather than by string tokens.
"""

from __future__ import annotations

from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

DEFAULT_URI_AUTHORITY = parse_tagging_authority("local@propstore,2026")


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
