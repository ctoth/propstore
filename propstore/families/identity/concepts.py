"""Deterministic identity for concepts minted during source promotion.

A source branch proposes concepts in its own local vocabulary. When the branch
is promoted, a proposal that matches no existing canonical concept is minted as a
NEW canonical :class:`~propstore.families.concepts.Concept`. Its ``concept_id`` is
``ps:concept:<sha256 of the normalised local handle>`` — derived from the
concept's handle, not minted by storage. Two proposals whose handles normalise to
the same slug therefore derive the *same* id; ``resolve_source_concept_promotions``
reads that collision as an ambiguous mapping and quarantines it rather than
silently merging two rivals (the non-commitment discipline).
"""

from __future__ import annotations

import hashlib


def derive_concept_artifact_id(local_handle: str) -> str:
    """Derive a deterministic concept artifact id from a normalised handle.

    *local_handle* must already be a safe slug (e.g. via
    ``propstore.source.common.normalize_source_slug``); identity stays a pure
    hash so this module never imports the source subsystem.
    """

    digest = hashlib.sha256(local_handle.encode("utf-8")).hexdigest()
    return f"ps:concept:{digest}"
