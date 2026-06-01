"""Resolution helpers for conflicted concepts.

`ResolutionStrategy` chooses a winner among active claims. The active belief
space is computed by BoundWorld (Z3 condition solving); the reasoning backend
is only relevant when the strategy is ARGUMENTATION.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from propstore.core.environment import AuthoredJustificationStore, StanceStore
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
)
from propstore.families.claims.declaration import Claim
from propstore.core.labels import Label, SupportQuality
from propstore.world.assignment_selection_policy import (
    resolve_assignment_selection_merge,
)
from propstore.world.value_resolver import ClaimValueResolver
from propstore.world.types import (
    ArgumentationSemantics,
    BeliefSpace,
    ClaimSupportView,
    GroundingBundleStore,
    HasActiveGraph,
    HasATMSEngine,
    WorldStore,
    ReasoningBackend,
    RenderPolicy,
    ResolvedResult,
    ResolutionStrategy,
    ValueStatus,
    apply_decision_criterion,
    validate_backend_semantics,
)


@dataclass(frozen=True)
class ClaimProvenance:
    paper: str | None = None
    page: int | None = None
    payload: Mapping[str, object] = field(default_factory=dict)

    def to_json(self) -> str | None:
        data = self.to_dict()
        if not data:
            return None
        return json.dumps(data, sort_keys=True)


@dataclass(frozen=True)
class _ResolutionClaimView:
    id: ClaimId
    value: float | str | None
    provenance: ClaimProvenance | None
    sample_size: int | None
    confidence: float | None


def _claim_id(claim: Claim) -> ClaimId:
    return ClaimId(claim.id)


def _claim_provenance(claim: Claim) -> ClaimProvenance | None:
    return ClaimProvenance.from_components(
        paper=claim.source_paper,
        page=claim.provenance_page,
        provenance_json=claim.provenance_json,
    )


def _resolution_claim_view(claim: Claim) -> _ResolutionClaimView:
    return _ResolutionClaimView(
        id=_claim_id(claim),
        value=ClaimValueResolver.claim_value(claim),
        provenance=_claim_provenance(claim),
        sample_size=_claim_sample_size(claim),
        confidence=None,
    )


def _display_claim_id(store: WorldStore | None, claim_id: str | None) -> str | None:
    if claim_id is None:
        return None
    if store is None:
        return claim_id
    claim = store.get_claim(claim_id)
    if claim is not None:
        primary_logical_id = claim.primary_logical_id
        if isinstance(primary_logical_id, str) and primary_logical_id:
            return primary_logical_id
    return claim_id


def _resolve_recency(
    claims: Sequence[_ResolutionClaimView],
) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent date in provenance_json.

    If multiple claims share the same best date, returns ``(None, reason)``
    so that the caller treats the result as conflicted rather than silently
    picking an arbitrary winner.
    """
    best_date = ""
    dated_claims: list[tuple[str, str]] = []  # (claim_id, date)
    for c in claims:
        provenance = c.provenance
        if provenance is None:
            continue
        prov_data = provenance.to_dict()
        date = prov_data.get("date") if isinstance(prov_data, Mapping) else ""
        date = date or ""
        if isinstance(date, str) and date >= best_date:
            if date > best_date:
                best_date = date
                dated_claims = [(c.id, date)]
            else:
                dated_claims.append((c.id, date))
    if not dated_claims:
        return None, "no dates in provenance"
    if len(dated_claims) == 1:
        return dated_claims[0][0], f"most recent: {best_date}"
    tied_ids = [cid for cid, _ in dated_claims]
    return None, f"tied recency ({best_date}): {', '.join(tied_ids)}"


def _resolve_sample_size(
    claims: Sequence[_ResolutionClaimView],
) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample_size.

    If multiple claims share the same best sample_size, returns
    ``(None, reason)`` so that the caller treats the result as conflicted
    rather than silently picking an arbitrary winner.
    """
    best_n: int | None = None
    best_claims: list[str] = []
    for c in claims:
        n = c.sample_size
        if n is not None:
            if best_n is None or n > best_n:
                best_n = n
                best_claims = [c.id]
            elif n == best_n:
                best_claims.append(c.id)
    if not best_claims:
        return None, "no sample_size values"
    if len(best_claims) == 1:
        return best_claims[0], f"largest sample_size: {best_n}"
    return None, f"tied sample_size ({best_n}): {', '.join(best_claims)}"


def _resolve_claim_graph_argumentation(
    target_claims: Sequence[_ResolutionClaimView],
    active_claims: Sequence[_ResolutionClaimView],
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    active_graph=None,
) -> tuple[str | None, str | None]:
    """Resolve in the current claim-graph backend.

    The AF is built over the whole active belief space, then projected back
    to the target concept's active claims.
    """
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    from propstore.argumentation import (
        analyze_claim_graph,
        shared_analyzer_input_from_active_graph,
        shared_analyzer_input_from_store,
    )

    active_views = tuple(active_claims)
    target_views = tuple(target_claims)
    active_ids = {str(c.id) for c in active_views}
    target_ids = {str(c.id) for c in target_views}
    shared = (
        shared_analyzer_input_from_active_graph(active_graph, comparison=comparison)
        if active_graph is not None
        else shared_analyzer_input_from_store(world, active_ids, comparison=comparison)
    )
    result = analyze_claim_graph(
        shared,
        semantics=normalized_semantics,
        target_claim_ids=target_ids,
    )
    projection = result.projection

    if len(result.extensions) == 0:
        if normalized_semantics == ArgumentationSemantics.STABLE:
            return None, "no stable extensions"
        return None, f"no {normalized_semantics.value} extensions"

    survivors = frozenset(
        projection.survivor_claim_ids if projection is not None else ()
    )
    witness_claims = frozenset(
        projection.witness_claim_ids if projection is not None else ()
    )

    if len(survivors) == 0:
        if len(result.extensions) > 1:
            if witness_claims:
                return (
                    None,
                    f"no skeptically accepted claim in {normalized_semantics.value} extensions",
                )
            return (
                None,
                f"all target claims absent from every {normalized_semantics.value} extension",
            )
        return None, "all claims defeated"
    if len(survivors) == 1:
        winner = next(iter(survivors))
        return winner, f"sole survivor in {normalized_semantics.value} extension"

    return (
        None,
        f"{len(survivors)} claims survive in {normalized_semantics.value} extension",
    )


def _resolve_structured_argumentation(
    target_claims: Sequence[_ResolutionClaimView],
    active_claims: list[Claim],
    view: BeliefSpace,
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    link: str = "last",
) -> tuple[str | None, str | None]:
    """Resolve via the ASPIC structured-argument pipeline."""
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.ASPIC,
        semantics,
    )
    from propstore.aspic_bridge import build_aspic_projection
    from propstore.structured_projection import compute_structured_justified_arguments

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    if isinstance(view, ClaimSupportView):
        for claim in active_claims:
            claim_id = _claim_id(claim)
            support_metadata[claim_id] = view.claim_support(claim)

    if not isinstance(world, GroundingBundleStore):
        return None, "ASPIC backend requires a grounded bundle-capable store"

    active_ids = {str(_claim_id(claim)) for claim in active_claims}
    active_graph = view.active_graph if isinstance(view, HasActiveGraph) else None
    bundle = world.grounding_bundle()
    if active_graph is None:
        has_stance_surface = isinstance(world, StanceStore)
        stance_rows = (
            tuple(world.stances_between(active_ids)) if has_stance_surface else ()
        )
        has_authored_justification_surface = isinstance(
            world, AuthoredJustificationStore
        )
        authored_justifications = (
            tuple(world.justifications_for_claim_scope(active_ids))
            if has_authored_justification_surface
            else ()
        )
        has_grounded_rule_input = bool(
            bundle.source_rules
            or bundle.source_facts
            or bundle.arguments
            or bundle.projection_frames
        )
        if (
            (has_stance_surface or has_authored_justification_surface)
            and not stance_rows
            and not authored_justifications
            and not has_grounded_rule_input
        ):
            return None, "no stance data"

    projection = build_aspic_projection(
        world,
        active_claims,
        bundle=bundle,
        support_metadata=support_metadata,
        comparison=comparison,
        link=link,
        active_graph=active_graph,
    )
    result = compute_structured_justified_arguments(
        projection,
        semantics=normalized_semantics,
        backend=ReasoningBackend.ASPIC,
    )

    target_arg_ids = frozenset(
        arg_id
        for claim in target_claims
        for arg_id in projection.claim_to_argument_ids.get(claim.id, ())
    )
    if isinstance(result, frozenset):
        survivor_args = result & target_arg_ids
    else:
        if not result:
            if normalized_semantics == ArgumentationSemantics.STABLE:
                return None, "no stable ASPIC+ extensions"
            return None, f"no {normalized_semantics.value} ASPIC+ extensions"
        survivor_args = frozenset.intersection(*result) & target_arg_ids
        if len(survivor_args) == 0:
            credulous_args = frozenset().union(*result) & target_arg_ids
            if credulous_args:
                return None, (
                    f"no skeptically accepted claim in {normalized_semantics.value} ASPIC+ projection"
                )
            return None, (
                f"all target claims absent from every {normalized_semantics.value} ASPIC+ extension"
            )

    survivor_claims = {
        projection.argument_to_claim_id[arg_id] for arg_id in survivor_args
    }
    if len(survivor_claims) == 0:
        return None, "all ASPIC+ arguments defeated"
    if len(survivor_claims) == 1:
        winner = next(iter(survivor_claims))
        return winner, f"sole ASPIC+ survivor in {normalized_semantics.value} extension"

    return (
        None,
        f"{len(survivor_claims)} claims survive in {normalized_semantics.value} ASPIC+ projection",
    )


def _resolve_aspic_argumentation(
    target_claims: Sequence[_ResolutionClaimView],
    active_claims: list[Claim],
    view: BeliefSpace,
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    link: str = "last",
) -> tuple[str | None, str | None]:
    """Resolve via the canonical ASPIC+ backend."""
    return _resolve_structured_argumentation(
        target_claims,
        active_claims,
        view,
        world,
        semantics=semantics,
        comparison=comparison,
        link=link,
    )


def _resolve_praf(
    target_claims: Sequence[_ResolutionClaimView],
    active_claims: Sequence[_ResolutionClaimView],
    world: WorldStore,
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
    from propstore.argumentation import (
        analyze_praf,
        praf_query_parameters,
        shared_analyzer_input_from_active_graph,
        shared_analyzer_input_from_store,
    )

    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.PRAF,
        semantics,
    )

    target_views = tuple(target_claims)
    active_views = tuple(active_claims)
    active_ids = {str(c.id) for c in active_views}
    target_ids = {str(c.id) for c in target_views}

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
    query_parameters = praf_query_parameters(
        semantics=normalized_semantics,
        strategy=strategy,
        query_kind="argument_acceptance",
        inference_mode="credulous",
        target_claim_ids=target_ids,
    )
    result = analyze_praf(
        shared,
        semantics=normalized_semantics,
        strategy=query_parameters.strategy,
        query_kind=query_parameters.query_kind,
        inference_mode=query_parameters.inference_mode,
        queried_set=query_parameters.queried_set,
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
    omitted_target_arguments = tuple(
        sorted(set(metadata.get("omitted_arguments", ())) & target_ids)
    )
    if omitted_target_arguments:
        return (
            None,
            "PrAF target calibration omitted for "
            f"{', '.join(omitted_target_arguments)} via {strategy_used} ({semantics})",
            {},
        )

    if acceptance is None:
        extension_probability = metadata.get("extension_probability")
        best_claims = list(
            projection.survivor_claim_ids if projection is not None else ()
        )
        if len(best_claims) == 1:
            winner = best_claims[0]
            probability_text = (
                "unknown"
                if extension_probability is None
                else f"{float(extension_probability):.4f}"
            )
            return (
                winner,
                f"PrAF extension probability ({probability_text}) "
                f"via {strategy_used} ({semantics})",
                None,
            )
        if not best_claims:
            return (
                None,
                f"no target extension witness via {strategy_used} ({semantics})",
                None,
            )
        return (
            None,
            f"{len(best_claims)} claims share extension-probability witness "
            f"via {strategy_used} ({semantics})",
            None,
        )

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
        claim_lookup = {
            claim_id: shared.claims_by_id[claim_id]
            for claim_id in target_ids
            if claim_id in shared.claims_by_id
        }
        decision_values: dict[str, float | None] = {}
        for cid in best_claims:
            claim = claim_lookup.get(cid)
            if claim is None or claim.opinion is None:
                dv = apply_decision_criterion(
                    None,
                    None,
                    None,
                    None,
                    None,
                    criterion=decision_criterion,
                    pessimism_index=pessimism_index,
                )
            else:
                dv = apply_decision_criterion(
                    claim.opinion.b,
                    claim.opinion.d,
                    claim.opinion.u,
                    claim.opinion.a,
                    claim.confidence,
                    criterion=decision_criterion,
                    pessimism_index=pessimism_index,
                )
            # Unpack the tagged DecisionValue for numeric tiebreaking. The
            # provenance tag (.source) is intentionally discarded here:
            # tiebreaker arithmetic does not care whether the value came
            # from a calibrated opinion or a raw confidence-derived score. If
            # the source needs to surface in the resolution reason, that
            # is a separate plumbing concern.
            decision_values[cid] = dv.value

        # Filter to claims with non-None decision values
        scored = {cid: v for cid, v in decision_values.items() if v is not None}
        if scored:
            best_dv = max(scored.values())
            dv_winners = [
                cid
                for cid, v in scored.items()
                if math.isclose(v, best_dv, rel_tol=1e-9)
            ]
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
    target_claims: Sequence[_ResolutionClaimView],
    view: BeliefSpace,
) -> tuple[str | None, str | None]:
    """Resolve by ATMS-supported status over the active belief space."""
    if not isinstance(view, HasATMSEngine):
        raise NotImplementedError(
            "ATMS backend requires a bound world with an ATMS engine"
        )

    engine = view.atms_engine()
    target_ids = {claim.id for claim in target_claims}
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
    world: WorldStore | None = None,
    overrides: dict[str, str] | None = None,
    reasoning_backend: ReasoningBackend | None = None,
    semantics: str | None = None,
    comparison: str | None = None,
    link: str | None = None,
    policy: RenderPolicy | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
    typed_concept_id = ConceptId(concept_id)
    vr = view.value_of(concept_id)

    if vr.status is ValueStatus.NO_CLAIMS:
        return ResolvedResult(concept_id=typed_concept_id, status=ValueStatus.NO_CLAIMS)

    if vr.status is ValueStatus.DETERMINED:
        determined_claim = _resolution_claim_view(vr.claims[0]) if vr.claims else None
        value = None if determined_claim is None else determined_claim.value
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.DETERMINED,
            value=value,
            claims=vr.claims,
        )

    if vr.status is not ValueStatus.CONFLICTED:
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=vr.status,
            claims=vr.claims,
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
        if link is None:
            link = policy.link
        # decision_criterion and pessimism_index are read inside
        # _resolve_praf() from the policy object directly.

    if reasoning_backend is None:
        reasoning_backend = ReasoningBackend.CLAIM_GRAPH
    if semantics is None:
        semantics = "grounded"
    if comparison is None:
        comparison = "elitist"
    if link is None:
        link = "last"
    if strategy is None:
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.CONFLICTED,
            claims=vr.claims,
            reason="no resolution strategy configured",
        )

    # Conflicted — apply strategy
    active = vr.claims
    active_views = tuple(_resolution_claim_view(claim) for claim in active)
    active_claims = list(view.active_claims())
    active_claim_views = tuple(_resolution_claim_view(claim) for claim in active_claims)
    winner_id: str | None = None
    reason: str | None = None
    _acceptance_probs: dict[str, float] | None = None
    active_graph = view.active_graph if isinstance(view, HasActiveGraph) else None

    if strategy == ResolutionStrategy.OVERRIDE:
        override_map = {} if overrides is None else overrides
        override_id = override_map.get(concept_id)
        if override_id is None:
            return ResolvedResult(
                concept_id=typed_concept_id,
                status=ValueStatus.CONFLICTED,
                claims=active,
                reason="no override specified",
            )
        active_ids = {claim.id for claim in active_views}
        if override_id not in active_ids:
            raise ValueError(
                f"Override claim {override_id} is not an active claim for {concept_id}"
            )
        winner_id = override_id
        reason = f"override: {override_id}"

    elif strategy == ResolutionStrategy.RECENCY:
        winner_id, reason = _resolve_recency(active_views)

    elif strategy == ResolutionStrategy.SAMPLE_SIZE:
        winner_id, reason = _resolve_sample_size(active_views)

    elif strategy == ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE:
        if world is None:
            return ResolvedResult(
                concept_id=typed_concept_id,
                status=ValueStatus.CONFLICTED,
                claims=active,
                strategy=strategy.value,
                reason="assignment_selection_merge strategy requires an explicit artifact store",
            )
        winner_id, reason = resolve_assignment_selection_merge(
            active,
            active_claims,
            concept_id,
            world=world,
            policy=policy,
        )

    elif strategy == ResolutionStrategy.ARGUMENTATION:
        if world is None:
            return ResolvedResult(
                concept_id=typed_concept_id,
                status=ValueStatus.CONFLICTED,
                claims=active,
                reason="argumentation strategy requires an explicit artifact store",
            )
        _, semantics = validate_backend_semantics(reasoning_backend, semantics)
        if reasoning_backend == ReasoningBackend.CLAIM_GRAPH:
            winner_id, reason = _resolve_claim_graph_argumentation(
                active_views,
                active_claim_views,
                world,
                semantics=semantics,
                comparison=comparison,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.ASPIC:
            winner_id, reason = _resolve_aspic_argumentation(
                active_views,
                active_claims,
                view,
                world,
                semantics=semantics,
                comparison=comparison,
                link=link,
            )
        elif reasoning_backend == ReasoningBackend.PRAF:
            winner_id, reason, _acceptance_probs = _resolve_praf(
                active_views,
                active_claim_views,
                world,
                semantics=semantics,
                comparison=comparison,
                policy=policy,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.ATMS:
            winner_id, reason = _resolve_atms_support(active_views, view)
        else:
            raise NotImplementedError(
                f"Reasoning backend '{reasoning_backend.value}' is not implemented"
            )

    if winner_id is None:
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.CONFLICTED,
            claims=active,
            strategy=strategy.value,
            reason=reason,
            acceptance_probs=_acceptance_probs,
        )

    winning_claim = next(
        (claim for claim in active_views if claim.id == winner_id), None
    )
    value = None if winning_claim is None else winning_claim.value
    return ResolvedResult(
        concept_id=typed_concept_id,
        status=ValueStatus.RESOLVED,
        value=value,
        claims=active,
        winning_claim_id=ClaimId(winner_id),
        strategy=strategy.value,
        reason=reason,
        acceptance_probs=_acceptance_probs,
    )
