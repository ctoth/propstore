"""Deterministic identity for stances minted during source promotion.

A promoted :class:`~propstore.families.relations.Stance` is keyed by a
``stance_id`` derived from its *content* — the source/target claim ids and the
stance type. Identity is provenance-free: re-promoting the same edge yields the
same id, and two distinct edges never collide.
"""

from __future__ import annotations

from quire.hashing import canonical_json_sha256


def derive_stance_artifact_id(
    *,
    source_claim_id: str | None,
    target_claim_id: str | None,
    stance_type: str | None,
) -> str:
    """Derive a deterministic ``ps:stance:<sha>`` id from content."""

    payload = {
        "source_claim_id": source_claim_id,
        "target_claim_id": target_claim_id,
        "stance_type": stance_type,
    }
    return f"ps:stance:{canonical_json_sha256(payload)}"
