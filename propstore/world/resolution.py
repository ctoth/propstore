"""Resolution helpers for conflicted concepts.

`ResolutionStrategy` chooses a winner among active claims after the active
belief space has already been computed by the configured reasoning backend.
Run 1 keeps the existing claim-graph backend as the default.
"""

from __future__ import annotations

import json

from propstore.world.types import (
    ArtifactStore,
    BeliefSpace,
    ReasoningBackend,
    RenderPolicy,
    ResolvedResult,
    ResolutionStrategy,
)


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


def _resolve_claim_graph_argumentation(
    target_claims: list[dict],
    active_claims: list[dict],
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
) -> tuple[str | None, str | None]:
    """Resolve in the current claim-graph backend.

    The AF is built over the whole active belief space, then projected back
    to the target concept's active claims.
    """
    from propstore.argumentation import compute_claim_graph_justified_claims

    if not world.has_table("claim_stance"):
        return None, "no stance data"

    active_ids = {c["id"] for c in active_claims}
    target_ids = {c["id"] for c in target_claims}
    result = compute_claim_graph_justified_claims(
        world, active_ids,
        semantics=semantics,
        comparison=comparison,
        confidence_threshold=confidence_threshold,
    )

    if isinstance(result, frozenset):
        survivors = result & target_ids
    else:
        # For preferred/stable, take intersection across all extensions
        if not result:
            survivors = frozenset()
        else:
            survivors = frozenset.intersection(*result) & target_ids

    if len(survivors) == 0:
        return None, "all claims defeated"
    if len(survivors) == 1:
        winner = next(iter(survivors))
        return winner, f"sole survivor in {semantics} extension"

    return None, f"{len(survivors)} claims survive in {semantics} extension"


def resolve(
    view: BeliefSpace,
    concept_id: str,
    strategy: ResolutionStrategy | None = None,
    *,
    world: ArtifactStore | None = None,
    overrides: dict[str, str] | None = None,
    reasoning_backend: ReasoningBackend | None = None,
    semantics: str | None = None,
    comparison: str | None = None,
    confidence_threshold: float | None = None,
    policy: RenderPolicy | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
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

    if policy is not None:
        if strategy is None:
            strategy = policy.concept_strategies.get(concept_id, policy.strategy)
        if overrides is None:
            overrides = dict(policy.overrides)
        if reasoning_backend is None:
            reasoning_backend = policy.reasoning_backend
        if semantics is None:
            semantics = policy.semantics
        if comparison is None:
            comparison = policy.comparison
        if confidence_threshold is None:
            confidence_threshold = policy.confidence_threshold

    if reasoning_backend is None:
        reasoning_backend = ReasoningBackend.CLAIM_GRAPH
    if semantics is None:
        semantics = "grounded"
    if comparison is None:
        comparison = "elitist"
    if confidence_threshold is None:
        confidence_threshold = 0.5

    if strategy is None:
        return ResolvedResult(
            concept_id=concept_id, status="conflicted",
            claims=vr.claims, reason="no resolution strategy configured",
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
            return ResolvedResult(
                concept_id=concept_id, status="conflicted",
                claims=active, reason="argumentation strategy requires an explicit artifact store",
            )
        if reasoning_backend != ReasoningBackend.CLAIM_GRAPH:
            raise NotImplementedError(
                f"Reasoning backend '{reasoning_backend.value}' is not implemented"
            )
        winner_id, reason = _resolve_claim_graph_argumentation(
            active,
            view.active_claims(),
            world,
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
