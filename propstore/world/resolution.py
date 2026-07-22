"""Render-time resolution of conflicted concepts (5 strategies).

``resolve`` applies a :class:`~propstore.world.types.ResolutionStrategy` to a
concept that the belief space reports as ``CONFLICTED`` and chooses a winning
claim — or honestly reports that no winner could be selected. This is a pure
*render-time* policy over the full active corpus: every active claim enters
resolution regardless of its uncertainty, nothing is collapsed in storage, and a
different :class:`~propstore.world.types.RenderPolicy` can pick a different winner
over the very same data (CLAUDE.md non-commitment + honest ignorance).

The active belief space (which claims are active under the current bindings) is
computed upstream by the belief-space view; this module only chooses among the
already-active claims. The reasoning backend matters only for the
``ARGUMENTATION`` strategy.

Strategy map:

* ``OVERRIDE`` — the policy names the winning claim id directly.
* ``RECENCY`` — newest provenance date among the active claims.
* ``SAMPLE_SIZE`` — largest sample size among the active claims.
* ``ASSIGNMENT_SELECTION_MERGE`` — build a package
  :class:`~assignment_selection.SourceAssignment` per source branch and delegate
  the Konieczny-style merge to
  :func:`~propstore.world.assignment_selection_merge.solve_assignment_selection_merge`.
* ``ARGUMENTATION`` — backend-dispatched over the built analyzers: claim-graph
  (:func:`~propstore.core.analyzers.analyze_claim_graph`), ASPIC+/structured
  (:func:`~propstore.aspic_bridge.build_aspic_projection` +
  :func:`~propstore.structured_projection.compute_structured_justified_arguments`),
  PrAF (:func:`~propstore.core.analyzers.analyze_praf` + decision criteria), and
  ATMS support — the last reached only through the
  :class:`~propstore.world.types.HasATMSEngine` protocol, so resolution never
  imports the ATMS engine (``world.atms``/``world.bound``) and stays above it.

Substrate boundary: the assignment-selection merge value types (``Assignment``,
``SourceAssignment``, ``Result``) are the ``assignment_selection`` package's own
canonical spellings, used directly — there is no propstore mirror.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from assignment_selection import Assignment, SourceAssignment

from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import AuthoredJustificationStore
from propstore.core.id_types import ClaimId, to_claim_id, to_concept_id
from propstore.core.labels import Label, SupportMetadata, SupportQuality
from propstore.world.assignment_selection_merge import (
    AssignmentSelectionRequest,
    solve_assignment_selection_merge,
)
from propstore.world.types import (
    ArgumentationSemantics,
    BeliefSpace,
    ClaimSupportView,
    GroundingBundleStore,
    HasActiveGraph,
    HasATMSEngine,
    IntegrityConstraint,
    MergeOperator,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    ValueStatus,
    WorldStore,
    apply_decision_criterion,
    validate_backend_semantics,
)

if TYPE_CHECKING:
    from propstore.core.graph_types import ActiveWorldGraph


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _resolve_recency(
    claims: Sequence[ActiveClaim],
) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent ``date``.

    Absence is honest ignorance — the recency strategy treats a dateless claim
    as undatable rather than inventing a date. If multiple claims share the
    same best date, returns ``(None, reason)`` so the caller treats the result
    as conflicted rather than silently picking an arbitrary winner.
    """
    best_date = ""
    dated_claims: list[tuple[str, str]] = []  # (claim_id, date)
    for c in claims:
        date = c.date
        if date is None:
            continue
        if date >= best_date:
            if date > best_date:
                best_date = date
                dated_claims = [(str(c.claim_id), date)]
            else:
                dated_claims.append((str(c.claim_id), date))
    if not dated_claims:
        return None, "no dates in provenance"
    if len(dated_claims) == 1:
        return dated_claims[0][0], f"most recent: {best_date}"
    tied_ids = [cid for cid, _ in dated_claims]
    return None, f"tied recency ({best_date}): {', '.join(tied_ids)}"


def _resolve_sample_size(
    claims: Sequence[ActiveClaim],
) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample size.

    If multiple claims share the same best sample size, returns ``(None, reason)``
    so the caller treats the result as conflicted rather than silently picking an
    arbitrary winner.
    """
    best_n: int | None = None
    best_claims: list[str] = []
    for c in claims:
        n = _optional_int(c.sample_size)
        if n is None:
            continue
        if best_n is None or n > best_n:
            best_n = n
            best_claims = [str(c.claim_id)]
        elif n == best_n:
            best_claims.append(str(c.claim_id))
    if not best_claims:
        return None, "no sample_size values"
    if len(best_claims) == 1:
        return best_claims[0], f"largest sample_size: {best_n}"
    return None, f"tied sample_size ({best_n}): {', '.join(best_claims)}"


def _claim_concept_id(claim: ActiveClaim) -> str:
    concept_id = claim.concept_id
    if not concept_id:
        raise KeyError(
            "resolution requires each claim to have a non-empty value concept"
        )
    return concept_id


def _integrity_constraint_concept_ids(
    constraints: Sequence[IntegrityConstraint],
) -> set[str]:
    return {
        concept_id
        for constraint in constraints
        for concept_id in constraint.concept_ids
    }


def _filtered_assignment_selection_claims(
    active_claims: Sequence[ActiveClaim],
    policy: RenderPolicy | None,
) -> list[ActiveClaim]:
    branch_filter = None if policy is None else policy.branch_filter
    filtered: list[ActiveClaim] = []
    for claim in active_claims:
        if isinstance(claim.value, bool) or not isinstance(claim.value, int | float):
            continue
        branch = claim.branch
        if (
            branch_filter is not None
            and branch is not None
            and branch not in branch_filter
        ):
            continue
        filtered.append(claim)
    return filtered


def _build_assignment_selection_request(
    active_claims: Sequence[ActiveClaim],
    target_concept_id: str,
    *,
    policy: RenderPolicy | None,
) -> AssignmentSelectionRequest:
    """Build the package merge request from active claims plus explicit constraints.

    Sources are grouped by branch (or per-claim when unbranched); each source
    contributes a package :class:`~assignment_selection.Assignment` over the
    concepts it asserts. Only the policy's *explicit* integrity constraints flow
    through — concept-derived range/category constraints are not synthesised here
    because the rewrite ``Concept`` charter does not yet carry range/form
    information (see ``docs/gaps.md``); the explicit constraints are
    self-describing and need no concept-charter read.
    """
    branch_weights = None if policy is None else policy.branch_weights
    merge_operator = MergeOperator.SIGMA if policy is None else policy.merge_operator
    explicit_constraints = () if policy is None else tuple(policy.integrity_constraints)

    concept_ids = {_claim_concept_id(claim) for claim in active_claims}
    concept_ids.add(target_concept_id)
    concept_ids.update(_integrity_constraint_concept_ids(explicit_constraints))

    grouped: dict[str, dict[str, ActiveClaim]] = {}
    for claim in active_claims:
        concept_id = _claim_concept_id(claim)
        branch = claim.branch
        source_id = branch if branch else str(claim.claim_id)
        per_source = grouped.setdefault(source_id, {})
        if concept_id in per_source:
            raise ValueError(
                f"source '{source_id}' has multiple active claims for concept '{concept_id}'"
            )
        per_source[concept_id] = claim

    sources: list[SourceAssignment] = []
    for source_id, concept_claims in grouped.items():
        sample_claim = next(iter(concept_claims.values()))
        branch = sample_claim.branch
        weight = 1.0
        if branch_weights is not None and branch is not None:
            weight = float(branch_weights.get(branch, 1.0))
        values: dict[str, object] = {}
        for concept_id, claim in concept_claims.items():
            value = claim.value
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError(
                    "assignment-selection merge requires numeric claim values"
                )
            values[concept_id] = float(value)
        sources.append(
            SourceAssignment(
                source_id=source_id,
                assignment=Assignment(values=values),
                weight=weight,
            )
        )

    return AssignmentSelectionRequest(
        concept_ids=tuple(sorted(concept_ids)),
        sources=tuple(sources),
        integrity_constraints=explicit_constraints,
        operator=merge_operator,
    )


def _resolve_assignment_selection_merge(
    target_claims: Sequence[ActiveClaim],
    active_claims: Sequence[ActiveClaim],
    concept_id: str,
    *,
    policy: RenderPolicy | None = None,
) -> tuple[str | None, str | None]:
    filtered = _filtered_assignment_selection_claims(active_claims, policy)
    if not filtered:
        return None, "no assignment-selection merge sources after branch filter"
    try:
        request = _build_assignment_selection_request(
            filtered, concept_id, policy=policy
        )
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)

    try:
        result = solve_assignment_selection_merge(request)
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)
    if not result.winners:
        return None, result.reason

    target_values = {winner.value_for(concept_id) for winner in result.winners}
    if len(target_values) != 1:
        return None, (
            f"{len(result.winners)} assignment-selection merge assignments "
            "disagree on target value"
        )

    winning_value = next(iter(target_values))
    matching_claims = [
        claim
        for claim in target_claims
        if not isinstance(claim.value, bool)
        and isinstance(claim.value, int | float)
        and float(claim.value) == winning_value
    ]
    if len(matching_claims) != 1:
        return None, (
            f"merged target value represented by {len(matching_claims)} active claims"
        )

    return str(matching_claims[0].claim_id), (
        f"global assignment-selection merge ({request.operator.value}) winner "
        f"satisfies {len(request.integrity_constraints)} constraints across "
        f"{len(request.concept_ids)} concepts"
    )


def _resolve_claim_graph_argumentation(
    target_claims: Sequence[ActiveClaim],
    active_claims: Sequence[ActiveClaim],
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    active_graph: ActiveWorldGraph | None = None,
) -> tuple[str | None, str | None]:
    """Resolve in the claim-graph backend.

    The AF is built over the whole active belief space, then projected back to the
    target concept's active claims.
    """
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    from propstore.core.analyzers import (
        analyze_claim_graph,
        shared_analyzer_input_from_graph,
        shared_analyzer_input_from_store,
    )

    active_ids = {str(c.claim_id) for c in active_claims}
    target_ids = {str(c.claim_id) for c in target_claims}
    shared = (
        shared_analyzer_input_from_graph(active_graph, comparison=comparison)
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
                return None, (
                    f"no skeptically accepted claim in {normalized_semantics.value} extensions"
                )
            return None, (
                f"all target claims absent from every {normalized_semantics.value} extension"
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
    target_claims: Sequence[ActiveClaim],
    active_claims: Sequence[ActiveClaim],
    view: BeliefSpace,
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    link: str = "last",
) -> tuple[str | None, str | None]:
    """Resolve via the ASPIC+ structured-argument pipeline."""
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.ASPIC,
        semantics,
    )
    from propstore.aspic_bridge import build_aspic_projection
    from propstore.structured_projection import compute_structured_justified_arguments

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    if isinstance(view, ClaimSupportView):
        for claim in active_claims:
            support_metadata[str(claim.claim_id)] = view.claim_support(claim)

    if not isinstance(world, GroundingBundleStore):
        return None, "ASPIC backend requires a grounded bundle-capable store"

    active_ids = {str(claim.claim_id) for claim in active_claims}
    active_graph = (
        view.active_world_graph() if isinstance(view, HasActiveGraph) else None
    )
    bundle = world.grounding_bundle()
    if active_graph is None:
        # WorldStore always exposes ``stances_between``; only the authored-
        # justification surface is optional.
        stance_rows = tuple(world.stances_between(active_ids))
        has_authored_justification_surface = isinstance(
            world, AuthoredJustificationStore
        )
        authored_justifications = (
            tuple(world.justifications_for_claim_scope(active_ids))
            if has_authored_justification_surface
            else ()
        )
        has_grounded_rule_input = bool(
            bundle.source_rules or bundle.source_facts or bundle.arguments
        )
        if (
            not stance_rows
            and not authored_justifications
            and not has_grounded_rule_input
        ):
            return None, "no stance data"

    metadata: SupportMetadata | None = support_metadata or None
    projection = build_aspic_projection(
        world,
        active_claims,
        bundle=bundle,
        support_metadata=metadata,
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
        for arg_id in projection.claim_to_argument_ids.get(str(claim.claim_id), ())
    )
    if isinstance(result, frozenset):
        survivor_args = result & target_arg_ids
    else:
        if not result:
            if normalized_semantics == ArgumentationSemantics.STABLE:
                return None, "no stable ASPIC+ extensions"
            return None, f"no {normalized_semantics.value} ASPIC+ extensions"
        skeptical: frozenset[str] = result[0]
        credulous: frozenset[str] = frozenset()
        for extension in result:
            skeptical = skeptical & extension
            credulous = credulous | extension
        survivor_args = skeptical & target_arg_ids
        if len(survivor_args) == 0:
            credulous_args = credulous & target_arg_ids
            if credulous_args:
                return None, (
                    f"no skeptically accepted claim in {normalized_semantics.value} "
                    "ASPIC+ projection"
                )
            return None, (
                f"all target claims absent from every {normalized_semantics.value} "
                "ASPIC+ extension"
            )

    survivor_claims = {
        projection.argument_to_claim_id[arg_id] for arg_id in survivor_args
    }
    if len(survivor_claims) == 0:
        return None, "all ASPIC+ arguments defeated"
    if len(survivor_claims) == 1:
        winner = next(iter(survivor_claims))
        return winner, f"sole ASPIC+ survivor in {normalized_semantics.value} extension"

    return None, (
        f"{len(survivor_claims)} claims survive in {normalized_semantics.value} "
        "ASPIC+ projection"
    )


def _resolve_aspic_argumentation(
    target_claims: Sequence[ActiveClaim],
    active_claims: Sequence[ActiveClaim],
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
    target_claims: Sequence[ActiveClaim],
    active_claims: Sequence[ActiveClaim],
    world: WorldStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    policy: RenderPolicy | None = None,
    active_graph: ActiveWorldGraph | None = None,
) -> tuple[str | None, str | None, dict[str, float] | None]:
    """Resolve via Probabilistic Argumentation Framework.

    Per Li et al. (2012): build PrAF from opinion-annotated stances, compute
    acceptance probabilities, determine the winner by highest acceptance
    probability among competing claims. Ties are broken by the policy's decision
    criterion over each claim's opinion (Denoeux 2019, pp.17-18).

    Returns ``(winner_id, reason, acceptance_probs)``.
    """
    from propstore.core.analyzers import (
        analyze_praf,
        praf_query_parameters,
        shared_analyzer_input_from_graph,
        shared_analyzer_input_from_store,
    )

    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.PRAF,
        semantics,
    )

    active_ids = {str(c.claim_id) for c in active_claims}
    target_ids = {str(c.claim_id) for c in target_claims}

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
        shared_analyzer_input_from_graph(active_graph, comparison=comparison)
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

    # Tiebreaker: apply the decision criterion to each tied claim's opinion per
    # Denoeux (2019, pp.17-18). Pignistic ties remain ties (backward compatible)
    # because PrAF acceptance already uses expectations.
    decision_criterion = "pignistic"
    pessimism_index = 0.5
    if policy is not None:
        decision_criterion = policy.decision_criterion
        pessimism_index = policy.pessimism_index

    if len(best_claims) > 1 and decision_criterion != "pignistic":
        claim_lookup = {str(c.claim_id): c for c in target_claims}
        decision_values: dict[str, float | None] = {}
        for cid in best_claims:
            claim = claim_lookup.get(cid)
            # The DecisionValue provenance tag (.source) is intentionally
            # discarded here: tiebreaker arithmetic does not care whether the
            # value came from a calibrated opinion or a confidence fallback.
            dv = apply_decision_criterion(
                None if claim is None else claim.opinion_belief,
                None if claim is None else claim.opinion_disbelief,
                None if claim is None else claim.opinion_uncertainty,
                None if claim is None else claim.opinion_base_rate,
                None if claim is None else claim.confidence,
                criterion=decision_criterion,
                pessimism_index=pessimism_index,
            )
            decision_values[cid] = dv.value

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
        f"{len(best_claims)} claims tied at acceptance {best_prob:.4f} "
        f"via {strategy_used} ({semantics})",
        acceptance,
    )


def _resolve_atms_support(
    target_claims: Sequence[ActiveClaim],
    view: BeliefSpace,
) -> tuple[str | None, str | None]:
    """Resolve by ATMS-supported status over the active belief space.

    The ATMS engine is reached only through the
    :class:`~propstore.world.types.HasATMSEngine` protocol — resolution never
    imports ``world.atms`` or ``world.bound`` and so stays above the engine.
    """
    if not isinstance(view, HasATMSEngine):
        raise NotImplementedError(
            "ATMS backend requires a bound world with an ATMS engine"
        )

    engine = view.atms_engine()
    target_ids = {str(c.claim_id) for c in target_claims}
    supported = engine.supported_claim_ids() & target_ids
    if len(supported) == 0:
        return None, "all ATMS-supported claims defeated"
    if len(supported) == 1:
        return next(iter(supported)), "sole ATMS-supported claim survives"
    return None, f"{len(supported)} claims remain ATMS-supported"


def _resolve_override(
    concept_id: str,
    active_views: Sequence[ActiveClaim],
    overrides: Mapping[str, str] | None,
) -> tuple[str | None, str | None]:
    override_map: Mapping[str, str] = {} if overrides is None else overrides
    override_id = override_map.get(concept_id)
    if override_id is None:
        return None, "no override specified"
    active_ids = {str(c.claim_id) for c in active_views}
    if override_id not in active_ids:
        raise ValueError(
            f"Override claim {override_id} is not an active claim for {concept_id}"
        )
    return override_id, f"override: {override_id}"


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
    """Apply a resolution strategy to a conflicted concept.

    Render-time only: a concept that the view reports as ``DETERMINED`` or
    ``NO_CLAIMS`` passes straight through; resolution runs only when the concept
    is ``CONFLICTED``. Every active claim participates regardless of uncertainty,
    and a different ``policy`` may select a different winner over the same corpus.
    """
    typed_concept_id = to_concept_id(concept_id)
    vr = view.value_of(concept_id)

    if vr.status is ValueStatus.NO_CLAIMS:
        return ResolvedResult(concept_id=typed_concept_id, status=ValueStatus.NO_CLAIMS)

    if vr.status is ValueStatus.DETERMINED:
        value = vr.claims[0].value if vr.claims else None
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.DETERMINED,
            value=value,
            claims=vr.claims,
        )

    if vr.status is not ValueStatus.CONFLICTED:
        return ResolvedResult(
            concept_id=typed_concept_id, status=vr.status, claims=vr.claims
        )

    if policy is not None:
        if strategy is None:
            strategy = policy.concept_strategies.get(concept_id, policy.strategy)
        if overrides is None:
            overrides = dict(policy.overrides)
        if reasoning_backend is None:
            reasoning_backend = policy.reasoning_backend
        if semantics is None:
            semantics = policy.semantics.value
        if comparison is None:
            comparison = policy.comparison
        if link is None:
            link = policy.link

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

    active = vr.claims
    active_claim_rows = tuple(view.active_claims())
    winner_id: str | None = None
    reason: str | None = None
    acceptance_probs: dict[str, float] | None = None
    active_graph = (
        view.active_world_graph() if isinstance(view, HasActiveGraph) else None
    )

    if strategy == ResolutionStrategy.OVERRIDE:
        winner_id, reason = _resolve_override(concept_id, active, overrides)

    elif strategy == ResolutionStrategy.RECENCY:
        winner_id, reason = _resolve_recency(active)

    elif strategy == ResolutionStrategy.SAMPLE_SIZE:
        winner_id, reason = _resolve_sample_size(active)

    elif strategy == ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE:
        winner_id, reason = _resolve_assignment_selection_merge(
            active,
            active_claim_rows,
            concept_id,
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
        _, normalized = validate_backend_semantics(reasoning_backend, semantics)
        semantics = normalized.value
        if reasoning_backend == ReasoningBackend.CLAIM_GRAPH:
            winner_id, reason = _resolve_claim_graph_argumentation(
                active,
                active_claim_rows,
                world,
                semantics=semantics,
                comparison=comparison,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.ASPIC:
            winner_id, reason = _resolve_aspic_argumentation(
                active,
                list(active_claim_rows),
                view,
                world,
                semantics=semantics,
                comparison=comparison,
                link=link,
            )
        elif reasoning_backend == ReasoningBackend.PRAF:
            winner_id, reason, acceptance_probs = _resolve_praf(
                active,
                active_claim_rows,
                world,
                semantics=semantics,
                comparison=comparison,
                policy=policy,
                active_graph=active_graph,
            )
        elif reasoning_backend == ReasoningBackend.ATMS:
            winner_id, reason = _resolve_atms_support(active, view)

    if winner_id is None:
        return ResolvedResult(
            concept_id=typed_concept_id,
            status=ValueStatus.CONFLICTED,
            claims=active,
            strategy=strategy.value,
            reason=reason,
            acceptance_probs=acceptance_probs,
        )

    winning_claim = next((c for c in active if str(c.claim_id) == winner_id), None)
    winning_claim_id: ClaimId = to_claim_id(winner_id)
    value = None if winning_claim is None else winning_claim.value
    return ResolvedResult(
        concept_id=typed_concept_id,
        status=ValueStatus.RESOLVED,
        value=value,
        claims=active,
        winning_claim_id=winning_claim_id,
        strategy=strategy.value,
        reason=reason,
        acceptance_probs=acceptance_probs,
    )
