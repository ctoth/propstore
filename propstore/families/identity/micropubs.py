"""Content identity for propstore micropublication documents.

Kuhn & Dumontier 2014 motivates embedding hashes in URIs for verifiable
artifacts and reference trees (pp. 1-2). Their implemented modules are
byte-level files or RDF graphs (p. 7), while propstore micropubs are
typed JSON/YAML documents. This module therefore defines a propstore-specific
canonical payload and feeds it to the ni-URI primitive; it does not claim full
Kuhn RA/FA module compatibility.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from propstore.families.micropublications.declaration import MicropublicationDocument
from propstore.uri import compute_ni_uri
from quire import canonical_json_sha256
from quire.documents import document_to_payload

MICROPUB_IDENTITY_EXCLUDED_FIELDS = ("artifact_id", "version_id")
MICROPUB_SORTED_STRING_LIST_FIELDS = ("claims", "assumptions")
MICROPUB_SORTED_DICT_LIST_FIELDS = ("evidence",)


def canonicalize_micropub_for_identity(
    document: MicropublicationDocument,
) -> dict[str, Any]:
    """Return semantic micropub content used for content identity.

    Recursive identity fields are excluded because Kuhn's self-reference
    treatment first hashes a representation with the future artifact code
    abstracted away, then verifies by reproducing that abstraction
    (p. 6).
    """
    canonical_payload = document_to_payload(document)
    if not isinstance(canonical_payload, dict):
        raise TypeError("micropublication identity payload must be a mapping")
    canonical = copy.deepcopy(canonical_payload)
    for field in MICROPUB_IDENTITY_EXCLUDED_FIELDS:
        canonical.pop(field, None)

    for field in MICROPUB_SORTED_STRING_LIST_FIELDS:
        value = canonical.get(field)
        if isinstance(value, list):
            canonical[field] = sorted(item for item in value if isinstance(item, str))

    for field in MICROPUB_SORTED_DICT_LIST_FIELDS:
        value = canonical.get(field)
        if isinstance(value, list):
            canonical[field] = sorted(
                (item for item in value if isinstance(item, dict)),
                key=_canonical_json_sort_key,
            )

    return canonical


def micropub_artifact_id(document: MicropublicationDocument) -> str:
    return compute_ni_uri(canonical_micropub_payload(document))


def micropub_version_id(document: MicropublicationDocument) -> str:
    return canonical_json_sha256(canonicalize_micropub_for_identity(document))


def _canonical_json_sort_key(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
