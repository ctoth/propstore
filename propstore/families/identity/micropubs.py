"""Content identity for source-branch micropublication bundles.

Kuhn & Dumontier 2014 motivate embedding a content hash in the artifact's own
URI for verifiable nanopublications and reference trees (pp. 1-2). Their modules
are byte-level files or RDF graphs (p. 7); a propstore source micropub is a typed
struct, so this module defines a deterministic canonical payload for the bundle
and feeds it to the ``ni:`` URI primitive. It does not claim full Kuhn RA/FA
module compatibility.

The recursive identity fields (``artifact_id`` / ``version_id``) are excluded
before hashing — Kuhn's self-reference treatment hashes a representation with the
future artifact code abstracted away, then verifies by reproducing that
abstraction (p. 6). The artifact id is therefore content identity, never a
logical handle, and is provenance-free in the sense that re-authoring identical
bundle content yields the same id regardless of which source minted it.
"""

from __future__ import annotations

import json
from typing import TypeGuard

import msgspec

from quire.canonical import canonical_json_sha256

from propstore.families.sources import SourceMicropublicationDocument
from propstore.uri import compute_ni_uri

MICROPUB_IDENTITY_EXCLUDED_FIELDS = ("artifact_id", "version_id")
MICROPUB_SORTED_STRING_LIST_FIELDS = ("claims", "assumptions")
MICROPUB_SORTED_DICT_LIST_FIELDS = ("evidence",)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    """Narrow a decoded JSON value to ``list[object]`` without a cast.

    ``isinstance`` on a bare ``list`` narrows to ``list[Unknown]``, which strict
    pyright rejects; this restores the element type as ``object`` (the one
    TypeGuard the canonicalization needs, mirroring
    :mod:`propstore.families.identity.claims`).
    """

    return isinstance(value, list)


def _is_str_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    """Narrow a decoded JSON value to ``dict[str, object]`` without a cast."""

    return isinstance(value, dict)


def canonicalize_micropub_for_identity(
    document: SourceMicropublicationDocument,
) -> dict[str, object]:
    """Return the semantic micropub content used for content identity.

    Drops the recursive identity fields, then orders the non-semantic list
    fields (the claim/assumption handle sets and the evidence entries) so that a
    bundle's identity is independent of authoring order.
    """

    canonical = msgspec.json.decode(
        msgspec.json.encode(document), type=dict[str, object]
    )
    for field in MICROPUB_IDENTITY_EXCLUDED_FIELDS:
        canonical.pop(field, None)

    for field in MICROPUB_SORTED_STRING_LIST_FIELDS:
        value = canonical.get(field)
        if _is_object_list(value):
            canonical[field] = sorted(item for item in value if isinstance(item, str))

    for field in MICROPUB_SORTED_DICT_LIST_FIELDS:
        value = canonical.get(field)
        if _is_object_list(value):
            canonical[field] = sorted(
                (item for item in value if _is_str_object_dict(item)),
                key=_canonical_json_sort_key,
            )

    return canonical


def canonical_micropub_payload(document: SourceMicropublicationDocument) -> bytes:
    """The exact canonical bytes the bundle's ``ni:`` URI verifies against."""

    return json.dumps(
        canonicalize_micropub_for_identity(document),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def micropub_artifact_id(document: SourceMicropublicationDocument) -> str:
    """The ``ni:///sha-256;...`` trusty URI identifying the bundle's content."""

    return compute_ni_uri(canonical_micropub_payload(document))


def micropub_version_id(document: SourceMicropublicationDocument) -> str:
    """The ``sha256:`` content version id of the bundle."""

    return canonical_json_sha256(canonicalize_micropub_for_identity(document))


def _canonical_json_sort_key(value: dict[str, object]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
