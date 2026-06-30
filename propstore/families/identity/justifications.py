"""Deterministic identity for justifications minted during source promotion.

A promoted :class:`~propstore.families.justifications.Justification` is keyed by a
``justification_id`` derived from its *content* — the conclusion, the (order-
insensitive) premises, and the rule kind/strength. Identity is provenance-free:
re-promoting the same argument yields the same id, and two distinct arguments
never collide.
"""

from __future__ import annotations

from collections.abc import Sequence

from quire.canonical import canonical_json_sha256


def derive_justification_artifact_id(
    *,
    conclusion: str | None,
    premises: Sequence[str],
    rule_kind: str | None,
    rule_strength: str | None,
) -> str:
    """Derive a deterministic ``ps:justification:<sha>`` id from content."""

    payload = {
        "conclusion": conclusion,
        "premises": sorted(premises),
        "rule_kind": rule_kind,
        "rule_strength": rule_strength,
    }
    return f"ps:justification:{canonical_json_sha256(payload)}"
