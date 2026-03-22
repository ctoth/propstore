"""Resolution strategy helpers for conflicted concepts."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from propstore.world.types import (
    ClaimView,
    ResolvedResult,
    ResolutionStrategy,
)

if TYPE_CHECKING:
    from propstore.world.model import WorldModel


def _resolve_recency(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent date in provenance_json."""
    best_id = None
    best_date = ""
    for c in claims:
        prov = c.get("provenance_json")
        if not prov:
            continue
        try:
            prov_data = json.loads(prov) if isinstance(prov, str) else prov
        except (json.JSONDecodeError, TypeError):
            continue
        date = prov_data.get("date") or ""
        if isinstance(date, str) and date > best_date:
            best_date = date
            best_id = c["id"]
    if best_id is None:
        return None, "no dates in provenance"
    return best_id, f"most recent: {best_date}"


def _resolve_sample_size(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample_size."""
    best_id = None
    best_n: int | None = None
    for c in claims:
        n = c.get("sample_size")
        if n is not None and (best_n is None or n > best_n):
            best_n = n
            best_id = c["id"]
    if best_id is None:
        return None, "no sample_size values"
    return best_id, f"largest sample_size: {best_n}"


_STANCE_WEIGHTS: dict[str, float] = {
    "supports": 1.0,
    "explains": 0.5,
    "rebuts": -1.0,
    "undercuts": -1.0,
    "undermines": -0.5,
}


def _resolve_stance(claims: list[dict], world: WorldModel) -> tuple[str | None, str | None]:
    """Pick the claim with the highest weighted stance score.

    Stance types have different weights (see _STANCE_WEIGHTS).
    Supersedes is handled specially: if claim A supersedes claim B
    and both are in contention, A wins outright.
    """
    scores: dict[str, float] = {c["id"]: 0.0 for c in claims}
    claim_ids = set(scores.keys())

    if not world._has_table("claim_stance"):
        return None, "no stance data"

    # Check for supersession first — trumps scoring
    for claim_id in claim_ids:
        rows = world._conn.execute(
            "SELECT claim_id FROM claim_stance "
            "WHERE target_claim_id = ? AND stance_type = 'supersedes'",
            (claim_id,),
        ).fetchall()
        for row in rows:
            if row["claim_id"] in claim_ids:
                return row["claim_id"], f"supersedes {claim_id}"

    # Weighted scoring for remaining types
    for claim_id in claim_ids:
        rows = world._conn.execute(
            "SELECT stance_type FROM claim_stance WHERE target_claim_id = ?",
            (claim_id,),
        ).fetchall()
        for row in rows:
            weight = _STANCE_WEIGHTS.get(row["stance_type"], 0.0)
            scores[claim_id] += weight

    if not scores:
        return None, "no stance data"

    max_score = max(scores.values())
    winners = [cid for cid, s in scores.items() if s == max_score]
    if len(winners) > 1:
        return None, f"tied stance scores: {max_score}"
    return winners[0], f"net stance score: {max_score}"


def resolve(
    view: ClaimView,
    concept_id: str,
    strategy: ResolutionStrategy,
    *,
    world: WorldModel | None = None,
    overrides: dict[str, str] | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
    from propstore.world.bound import BoundWorld
    from propstore.world.hypothetical import HypotheticalWorld

    vr = view.value_of(concept_id)

    if vr.status == "no_claims":
        return ResolvedResult(concept_id=concept_id, status="no_claims")

    if vr.status == "determined":
        value = vr.claims[0].get("value") if vr.claims else None
        return ResolvedResult(
            concept_id=concept_id, status="determined",
            value=value, claims=vr.claims,
        )

    if vr.status != "conflicted":
        return ResolvedResult(
            concept_id=concept_id, status=vr.status, claims=vr.claims,
        )

    # Conflicted — apply strategy
    active = vr.claims
    winner_id: str | None = None
    reason: str | None = None

    if strategy == ResolutionStrategy.OVERRIDE:
        override_id = (overrides or {}).get(concept_id)
        if override_id is None:
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="no override specified",
            )
        active_ids = {c["id"] for c in active}
        if override_id not in active_ids:
            raise ValueError(
                f"Override claim {override_id} is not an active claim for {concept_id}"
            )
        winner_id = override_id
        reason = f"override: {override_id}"

    elif strategy == ResolutionStrategy.RECENCY:
        winner_id, reason = _resolve_recency(active)

    elif strategy == ResolutionStrategy.SAMPLE_SIZE:
        winner_id, reason = _resolve_sample_size(active)

    elif strategy == ResolutionStrategy.STANCE:
        if world is None:
            # Try to get world from view
            if isinstance(view, BoundWorld):
                world = view._world
            elif isinstance(view, HypotheticalWorld):
                world = view._base._world
        if world is None:
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="no world for stance resolution",
            )
        winner_id, reason = _resolve_stance(active, world)

    if winner_id is None:
        return ResolvedResult(
            concept_id=concept_id, status="conflicted",
            claims=active, strategy=strategy.value, reason=reason,
        )

    winning_claim = next((c for c in active if c["id"] == winner_id), None)
    value = winning_claim.get("value") if winning_claim else None
    return ResolvedResult(
        concept_id=concept_id, status="resolved",
        value=value, claims=active,
        winning_claim_id=winner_id,
        strategy=strategy.value, reason=reason,
    )
