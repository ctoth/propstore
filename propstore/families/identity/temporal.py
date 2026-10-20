"""Content identity for transported authored temporal evidence.

An anchor relates a claim to bounds in one declared frame (Allen 1983); an
edge relates ordered description endpoints under its authored account (Lamport
1978). Replacing an endpoint changes that content, hence its identity. The
self id and provenance are excluded, as in the existing family identity owners.
Provenance remains on the document: unequal evidence at one content identity
must be rejected by merge admission, never discarded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from quire.canonical import canonical_json_sha256

if TYPE_CHECKING:
    from propstore.families.temporal import (
        DescriptionTemporalAnchorDoc,
        HappensBeforeEdgeDoc,
    )


def temporal_anchor_artifact_id(document: DescriptionTemporalAnchorDoc) -> str:
    """Identify the authored interval at a claim and declared frame."""

    payload = {
        "claim_id": document.claim_id,
        "frame_id": document.frame_id,
        "valid_from": document.valid_from,
        "valid_until": document.valid_until,
    }
    return f"ps:temporal-anchor:{canonical_json_sha256(payload)}"


def happens_before_artifact_id(document: HappensBeforeEdgeDoc) -> str:
    """Identify ordered endpoints and the account licensing their order."""

    payload = {
        "earlier_claim_id": document.earlier_claim_id,
        "later_claim_id": document.later_claim_id,
        "account": document.account.value,
    }
    return f"ps:happens-before:{canonical_json_sha256(payload)}"
