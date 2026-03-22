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


def _resolve_argumentation(
    claims: list[dict],
    world: WorldModel,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
) -> tuple[str | None, str | None]:
    """Resolve using ASPIC+ argumentation semantics.

    Builds a Dung AF from the stance graph filtered through preference
    ordering, computes the grounded extension, and picks the surviving
    claim (if exactly one survives for this concept).
    """
    from propstore.argumentation import compute_justified_claims

    if not world._has_table("claim_stance"):
        return None, "no stance data"

    claim_ids = {c["id"] for c in claims}
    result = compute_justified_claims(
        world._conn, claim_ids,
        semantics=semantics,
        comparison=comparison,
        confidence_threshold=confidence_threshold,
    )

    if semantics == "grounded":
        survivors = result & claim_ids
    else:
        # For preferred/stable, take intersection across all extensions
        if not result:
            survivors = frozenset()
        else:
            survivors = frozenset.intersection(*result) & claim_ids

    if len(survivors) == 0:
        return None, "all claims defeated"
    if len(survivors) == 1:
        winner = next(iter(survivors))
        return winner, f"sole survivor in {semantics} extension"

    return None, f"{len(survivors)} claims survive in {semantics} extension"


def resolve(
    view: ClaimView,
    concept_id: str,
    strategy: ResolutionStrategy,
    *,
    world: WorldModel | None = None,
    overrides: dict[str, str] | None = None,
    semantics: str = "grounded",
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
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

    elif strategy == ResolutionStrategy.ARGUMENTATION:
        if world is None:
            if isinstance(view, BoundWorld):
                world = view._world
            elif isinstance(view, HypotheticalWorld):
                world = view._base._world
        if world is None:
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="no world for argumentation",
            )
        winner_id, reason = _resolve_argumentation(
            active, world,
            semantics=semantics,
            comparison=comparison,
            confidence_threshold=confidence_threshold,
        )

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
