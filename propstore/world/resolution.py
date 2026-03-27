"""Resolution helpers for conflicted concepts.

`ResolutionStrategy` chooses a winner among active claims. The active belief
space is computed by BoundWorld (Z3 condition solving); the reasoning backend
is only relevant when the strategy is ARGUMENTATION.
"""

from __future__ import annotations

import json
import math

from propstore.world.types import (
    ArtifactStore,
    BeliefSpace,
    ReasoningBackend,
    RenderPolicy,
    ResolvedResult,
    ResolutionStrategy,
    ValueStatus,
    apply_decision_criterion,
)


def _resolve_recency(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent date in provenance_json.

    If multiple claims share the same best date, returns ``(None, reason)``
    so that the caller treats the result as conflicted rather than silently
    picking an arbitrary winner.
    """
    best_date = ""
    dated_claims: list[tuple[str, str]] = []  # (claim_id, date)
    for c in claims:
        prov = c.get("provenance_json")
        if not prov:
            continue
        try:
            prov_data = json.loads(prov) if isinstance(prov, str) else prov
        except (json.JSONDecodeError, TypeError):
            continue
        date = prov_data.get("date") or ""
        if isinstance(date, str) and date >= best_date:
            if date > best_date:
                best_date = date
                dated_claims = [(c["id"], date)]
            else:
                dated_claims.append((c["id"], date))
    if not dated_claims:
        return None, "no dates in provenance"
    if len(dated_claims) == 1:
        return dated_claims[0][0], f"most recent: {best_date}"
    tied_ids = [cid for cid, _ in dated_claims]
    return None, f"tied recency ({best_date}): {', '.join(tied_ids)}"


def _resolve_sample_size(claims: list[dict]) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample_size.

    If multiple claims share the same best sample_size, returns
    ``(None, reason)`` so that the caller treats the result as conflicted
    rather than silently picking an arbitrary winner.
    """
    best_n: int | None = None
    best_claims: list[str] = []
    for c in claims:
        n = c.get("sample_size")
        if n is not None:
            if best_n is None or n > best_n:
                best_n = n
                best_claims = [c["id"]]
            elif n == best_n:
                best_claims.append(c["id"])
    if not best_claims:
        return None, "no sample_size values"
    if len(best_claims) == 1:
        return best_claims[0], f"largest sample_size: {best_n}"
    return None, f"tied sample_size ({best_n}): {', '.join(best_claims)}"


def _resolve_claim_graph_argumentation(
    target_claims: list[dict],
    active_claims: list[dict],
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    active_graph=None,
) -> tuple[str | None, str | None]:
    """Resolve in the current claim-graph backend.

    The AF is built over the whole active belief space, then projected back
    to the target concept's active claims.
    """
    from propstore.core.analyzers import (
        analyze_claim_graph,
        shared_analyzer_input_from_active_graph,
        shared_analyzer_input_from_store,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data"

    active_ids = {c["id"] for c in active_claims}
    target_ids = {c["id"] for c in target_claims}
    shared = (
        shared_analyzer_input_from_active_graph(active_graph, comparison=comparison)
        if active_graph is not None
        else shared_analyzer_input_from_store(world, active_ids, comparison=comparison)
    )
    result = analyze_claim_graph(
        shared,
        semantics=semantics,
        target_claim_ids=target_ids,
    )
    projection = result.projection

    if len(result.extensions) == 0:
        if semantics == "stable":
            return None, "no stable extensions"
        return None, f"no {semantics} extensions"

    survivors = frozenset(projection.survivor_claim_ids if projection is not None else ())
    witness_claims = frozenset(projection.witness_claim_ids if projection is not None else ())

    if len(survivors) == 0:
        if len(result.extensions) > 1:
            if witness_claims:
                return None, f"no skeptically accepted claim in {semantics} extensions"
            return None, f"all target claims absent from every {semantics} extension"
        return None, "all claims defeated"
    if len(survivors) == 1:
        winner = next(iter(survivors))
        return winner, f"sole survivor in {semantics} extension"

    return None, f"{len(survivors)} claims survive in {semantics} extension"


def _resolve_structured_argumentation(
    target_claims: list[dict],
    active_claims: list[dict],
    view: BeliefSpace,
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
) -> tuple[str | None, str | None]:
    """Resolve via the first structured-argument projection backend."""
    from propstore.structured_argument import (
        build_structured_projection,
        compute_structured_justified_arguments,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data"

    support_metadata: dict[str, tuple[object | None, object]] = {}
    claim_support = getattr(view, "claim_support", None)
    if callable(claim_support):
        for claim in active_claims:
            claim_id = claim.get("id")
            if not claim_id:
                continue
            support_metadata[claim_id] = claim_support(claim)

    projection = build_structured_projection(
        world,
        active_claims,
        support_metadata=support_metadata,
        comparison=comparison,
        active_graph=getattr(view, "_active_graph", None),
    )
    result = compute_structured_justified_arguments(
        projection,
        semantics=semantics,
    )

    target_arg_ids = frozenset(
        arg_id
        for claim in target_claims
        for arg_id in projection.claim_to_argument_ids.get(claim["id"], ())
    )
    if isinstance(result, frozenset):
        survivor_args = result & target_arg_ids
    else:
        if not result:
            if semantics == "stable":
                return None, "no stable structured projection extensions"
            return None, f"no {semantics} structured projection extensions"
        survivor_args = frozenset.intersection(*result) & target_arg_ids
        if len(survivor_args) == 0:
            credulous_args = frozenset().union(*result) & target_arg_ids
            if credulous_args:
                return None, (
                    f"no skeptically accepted claim in {semantics} structured projection"
                )
            return None, (
                f"all target claims absent from every {semantics} structured projection"
            )

    survivor_claims = {
        projection.argument_to_claim_id[arg_id]
        for arg_id in survivor_args
    }
    if len(survivor_claims) == 0:
        return None, "all projected arguments defeated"
    if len(survivor_claims) == 1:
        winner = next(iter(survivor_claims))
        return winner, f"sole structured projection survivor in {semantics} extension"

    return None, f"{len(survivor_claims)} claims survive in {semantics} structured projection"


def _resolve_praf(
    target_claims: list[dict],
    active_claims: list[dict],
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    policy: RenderPolicy | None = None,
    active_graph=None,
) -> tuple[str | None, str | None, dict[str, float] | None]:
    """Resolve via Probabilistic Argumentation Framework.

    Per Li et al. (2012): build PrAF from opinion-annotated stances,
    compute acceptance probabilities, determine winner by highest
    acceptance probability among competing claims.

    Returns (winner_id, reason, acceptance_probs).
    """
    from propstore.core.analyzers import (
        analyze_praf,
        shared_analyzer_input_from_active_graph,
        shared_analyzer_input_from_store,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data", None

    active_ids = {c["id"] for c in active_claims}
    target_ids = {c["id"] for c in target_claims}

    # Extract PrAF parameters from policy
    strategy = "auto"
    mc_epsilon = 0.01
    mc_confidence = 0.95
    treewidth_cutoff = 12
    rng_seed: int | None = None

    if policy is not None:
        strategy = policy.praf_strategy
        mc_epsilon = policy.praf_mc_epsilon
        mc_confidence = policy.praf_mc_confidence
        treewidth_cutoff = policy.praf_treewidth_cutoff
        rng_seed = policy.praf_mc_seed

    shared = (
        shared_analyzer_input_from_active_graph(active_graph, comparison=comparison)
        if active_graph is not None
        else shared_analyzer_input_from_store(world, active_ids, comparison=comparison)
    )
    result = analyze_praf(
        shared,
        semantics=semantics,
        strategy=strategy,
        mc_epsilon=mc_epsilon,
        mc_confidence=mc_confidence,
        treewidth_cutoff=treewidth_cutoff,
        rng_seed=rng_seed,
        target_claim_ids=target_ids,
    )
    metadata = dict(result.metadata)
    acceptance = metadata["acceptance_probs"]
    strategy_used = metadata["strategy_used"]
    projection = result.projection

    # Filter to target claims and find winner by highest acceptance prob
    target_probs = {cid: acceptance.get(cid, 0.0) for cid in target_ids}

    if not target_probs:
        return None, "no target claims in PrAF", acceptance

    best_prob = max(target_probs.values())
    best_claims = list(projection.survivor_claim_ids if projection is not None else ())

    if len(best_claims) == 1:
        winner = best_claims[0]
        return (
            winner,
            f"highest PrAF acceptance ({best_prob:.4f}) via {strategy_used} ({semantics})",
            acceptance,
        )

    # Tiebreaker: apply decision criterion to each tied claim's opinion
    # components per Denoeux (2019, p.17-18).  Pignistic ties remain ties
    # (backward compatible) because PrAF already uses expectations.
    decision_criterion = "pignistic"
    pessimism_index = 0.5
    if policy is not None:
        decision_criterion = policy.decision_criterion
        pessimism_index = policy.pessimism_index

    if len(best_claims) > 1 and decision_criterion != "pignistic":
        # Build a lookup from claim id to claim dict
        claim_lookup = {c["id"]: c for c in target_claims}
        decision_values: dict[str, float | None] = {}
        for cid in best_claims:
            c = claim_lookup.get(cid, {})
            decision_values[cid] = apply_decision_criterion(
                c.get("opinion_belief"),
                c.get("opinion_disbelief"),
                c.get("opinion_uncertainty"),
                c.get("opinion_base_rate"),
                c.get("confidence"),
                criterion=decision_criterion,
                pessimism_index=pessimism_index,
            )

        # Filter to claims with non-None decision values
        scored = {cid: v for cid, v in decision_values.items() if v is not None}
        if scored:
            best_dv = max(scored.values())
            dv_winners = [cid for cid, v in scored.items()
                          if math.isclose(v, best_dv, rel_tol=1e-9)]
            if len(dv_winners) == 1:
                winner = dv_winners[0]
                return (
                    winner,
                    f"PrAF acceptance tie ({best_prob:.4f}) broken by "
                    f"{decision_criterion} ({best_dv:.4f}) via {strategy_used} ({semantics})",
                    acceptance,
                )

    return (
        None,
        f"{len(best_claims)} claims tied at acceptance {best_prob:.4f} via {strategy_used} ({semantics})",
        acceptance,
    )


def _resolve_atms_support(
    target_claims: list[dict],
    view: BeliefSpace,
) -> tuple[str | None, str | None]:
    """Resolve by ATMS-supported status over the active belief space."""
    atms_engine = getattr(view, "atms_engine", None)
    if not callable(atms_engine):
        raise NotImplementedError("ATMS backend requires a bound world with an ATMS engine")

    engine = atms_engine()
    target_ids = {claim["id"] for claim in target_claims}
    supported = engine.supported_claim_ids() & target_ids
    if len(supported) == 0:
        return None, "all ATMS-supported claims defeated"
    if len(supported) == 1:
        return next(iter(supported)), "sole ATMS-supported claim survives"
    return None, f"{len(supported)} claims remain ATMS-supported"


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
    policy: RenderPolicy | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
    vr = view.value_of(concept_id)

    if vr.status == "no_claims":
        return ResolvedResult(concept_id=concept_id, status=ValueStatus.NO_CLAIMS)

    if vr.status == "determined":
        value = vr.claims[0].get("value") if vr.claims else None
        return ResolvedResult(
            concept_id=concept_id, status=ValueStatus.DETERMINED,
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
        # decision_criterion and pessimism_index are read inside
        # _resolve_praf() from the policy object directly.

    if reasoning_backend is None:
        reasoning_backend = ReasoningBackend.CLAIM_GRAPH
    if semantics is None:
        semantics = "grounded"
    if comparison is None:
        comparison = "elitist"
    if strategy is None:
        return ResolvedResult(
            concept_id=concept_id, status=ValueStatus.CONFLICTED,
            claims=vr.claims, reason="no resolution strategy configured",
        )

    # Conflicted — apply strategy
    active = vr.claims
    winner_id: str | None = None
    reason: str | None = None
    _acceptance_probs: dict[str, float] | None = None
    active_graph = getattr(view, "_active_graph", None)

    if strategy == ResolutionStrategy.OVERRIDE:
        override_id = (overrides or {}).get(concept_id)
        if override_id is None:
            return ResolvedResult(
                concept_id=concept_id, status=ValueStatus.CONFLICTED,
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
                concept_id=concept_id, status=ValueStatus.CONFLICTED,
                claims=active, reason="argumentation strategy requires an explicit artifact store",
            )
        if reasoning_backend == ReasoningBackend.CLAIM_GRAPH:
            winner_id, reason = _resolve_claim_graph_argumentation(
                active,
                view.active_claims(),
                world,
                semantics=semantics,
                comparison=comparison,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.STRUCTURED_PROJECTION:
            winner_id, reason = _resolve_structured_argumentation(
                active,
                view.active_claims(),
                view,
                world,
                semantics=semantics,
                comparison=comparison,
            )
        elif reasoning_backend == ReasoningBackend.PRAF:
            winner_id, reason, _acceptance_probs = _resolve_praf(
                active,
                view.active_claims(),
                world,
                semantics=semantics,
                comparison=comparison,
                policy=policy,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.ATMS:
            winner_id, reason = _resolve_atms_support(active, view)
        else:
            raise NotImplementedError(
                f"Reasoning backend '{reasoning_backend.value}' is not implemented"
            )

    if winner_id is None:
        return ResolvedResult(
            concept_id=concept_id, status=ValueStatus.CONFLICTED,
            claims=active, strategy=strategy.value, reason=reason,
            acceptance_probs=_acceptance_probs,
        )

    winning_claim = next((c for c in active if c["id"] == winner_id), None)
    value = winning_claim.get("value") if winning_claim else None
    return ResolvedResult(
        concept_id=concept_id, status=ValueStatus.RESOLVED,
        value=value, claims=active,
        winning_claim_id=winner_id,
        strategy=strategy.value, reason=reason,
        acceptance_probs=_acceptance_probs,
    )
