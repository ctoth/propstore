"""Resolution helpers for conflicted concepts.

`ResolutionStrategy` chooses a winner among active claims. The active belief
space is computed by BoundWorld (Z3 condition solving); the reasoning backend
is only relevant when the strategy is ARGUMENTATION.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from propstore.cel_checker import ConceptInfo, KindType
from propstore.form_utils import kind_type_from_form_name
from propstore.world.labelled import Label, SupportQuality
from propstore.world.types import (
    ArgumentationSemantics,
    ArtifactStore,
    BeliefSpace,
    ClaimSupportView,
    HasActiveGraph,
    HasATMSEngine,
    ICMergeProblem,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeOperator,
    MergeSource,
    ReasoningBackend,
    RenderPolicy,
    ResolvedResult,
    ResolutionStrategy,
    ValueStatus,
    apply_decision_criterion,
    validate_backend_semantics,
)


@dataclass(frozen=True)
class _ResolutionClaimView:
    id: str
    value: float | str | None
    provenance_json: str | Mapping[str, object] | None
    sample_size: int | None
    opinion_belief: float | None
    opinion_disbelief: float | None
    opinion_uncertainty: float | None
    opinion_base_rate: float | None
    confidence: float | None


def _claim_id(claim: Mapping[str, object]) -> str:
    claim_id = claim.get("id")
    if not isinstance(claim_id, str) or not claim_id:
        raise KeyError("resolution requires each claim to have a non-empty string id")
    return claim_id


def _claim_value(claim: Mapping[str, object]) -> float | str | None:
    value = claim.get("value")
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return value
    return None


def _claim_optional_int(claim: Mapping[str, object], key: str) -> int | None:
    value = claim.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _claim_optional_float(claim: Mapping[str, object], key: str) -> float | None:
    value = claim.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _claim_provenance_json(claim: Mapping[str, object]) -> str | Mapping[str, object] | None:
    provenance = claim.get("provenance_json")
    if isinstance(provenance, str):
        return provenance
    if isinstance(provenance, Mapping):
        return provenance
    return None


def _resolution_claim_view(claim: Mapping[str, object]) -> _ResolutionClaimView:
    return _ResolutionClaimView(
        id=_claim_id(claim),
        value=_claim_value(claim),
        provenance_json=_claim_provenance_json(claim),
        sample_size=_claim_optional_int(claim, "sample_size"),
        opinion_belief=_claim_optional_float(claim, "opinion_belief"),
        opinion_disbelief=_claim_optional_float(claim, "opinion_disbelief"),
        opinion_uncertainty=_claim_optional_float(claim, "opinion_uncertainty"),
        opinion_base_rate=_claim_optional_float(claim, "opinion_base_rate"),
        confidence=_claim_optional_float(claim, "confidence"),
    )


def _coerce_resolution_claim(
    claim: _ResolutionClaimView | Mapping[str, object],
) -> _ResolutionClaimView:
    if isinstance(claim, _ResolutionClaimView):
        return claim
    return _resolution_claim_view(claim)


def _resolve_recency(
    claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
) -> tuple[str | None, str | None]:
    """Pick the claim with the most recent date in provenance_json.

    If multiple claims share the same best date, returns ``(None, reason)``
    so that the caller treats the result as conflicted rather than silently
    picking an arbitrary winner.
    """
    best_date = ""
    dated_claims: list[tuple[str, str]] = []  # (claim_id, date)
    for c in (_coerce_resolution_claim(claim) for claim in claims):
        prov = c.provenance_json
        if not prov:
            continue
        try:
            prov_data = json.loads(prov) if isinstance(prov, str) else prov
        except (json.JSONDecodeError, TypeError):
            continue
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
    claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
) -> tuple[str | None, str | None]:
    """Pick the claim with the largest sample_size.

    If multiple claims share the same best sample_size, returns
    ``(None, reason)`` so that the caller treats the result as conflicted
    rather than silently picking an arbitrary winner.
    """
    best_n: int | None = None
    best_claims: list[str] = []
    for c in (_coerce_resolution_claim(claim) for claim in claims):
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


def _normalized_form_parameters(concept: Mapping[str, object] | None) -> Mapping[str, object]:
    if concept is None:
        return {}
    raw = concept.get("form_parameters")
    if isinstance(raw, Mapping):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return parsed
    return {}


def _concept_integrity_constraints(
    world: ArtifactStore,
    concept_id: str,
) -> tuple[IntegrityConstraint, ...]:
    concept = world.get_concept(concept_id)
    if concept is None:
        return tuple()

    constraints: list[IntegrityConstraint] = []
    lower = concept.get("range_min")
    upper = concept.get("range_max")
    if lower is not None or upper is not None:
        constraints.append(
            IntegrityConstraint(
                kind=IntegrityConstraintKind.RANGE,
                concept_ids=(concept_id,),
                metadata={"lower": lower, "upper": upper},
                description="concept range",
            )
        )

    form_parameters = _normalized_form_parameters(concept)
    if concept.get("form") == "category":
        values = form_parameters.get("values")
        extensible = form_parameters.get("extensible", True)
        if isinstance(values, list | tuple) and not extensible:
            constraints.append(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CATEGORY,
                    concept_ids=(concept_id,),
                    metadata={
                        "allowed_values": tuple(str(value) for value in values),
                        "extensible": False,
                    },
                    description="non-extensible category value set",
                )
            )

    return tuple(constraints)


def _filtered_ic_merge_claim_rows(
    active_claim_rows: Sequence[Mapping[str, object]],
    policy: RenderPolicy | None,
) -> list[Mapping[str, object]]:
    branch_filter = None if policy is None else policy.branch_filter
    filtered: list[Mapping[str, object]] = []
    for claim in active_claim_rows:
        value = _claim_value(claim)
        if value is None:
            continue
        branch = claim.get("branch")
        if (
            branch_filter is not None
            and isinstance(branch, str)
            and branch not in branch_filter
        ):
            continue
        filtered.append(claim)
    return filtered


def _integrity_constraint_concept_ids(constraints: Sequence[IntegrityConstraint]) -> set[str]:
    return {
        concept_id
        for constraint in constraints
        for concept_id in constraint.concept_ids
    }


def _cel_registry_for_concepts(
    world: ArtifactStore,
    concept_ids: Sequence[str],
) -> dict[str, ConceptInfo]:
    registry: dict[str, ConceptInfo] = {}
    for concept_id in concept_ids:
        concept = world.get_concept(concept_id)
        if concept is None:
            continue
        canonical_name = concept.get("canonical_name")
        form = concept.get("form")
        if not isinstance(canonical_name, str) or not canonical_name:
            continue
        kind = kind_type_from_form_name(form)
        if kind is None:
            kind = KindType.QUANTITY
        form_parameters = _normalized_form_parameters(concept)
        registry[canonical_name] = ConceptInfo(
            id=concept_id,
            canonical_name=canonical_name,
            kind=kind,
            category_values=list(form_parameters.get("values") or ()),
            category_extensible=bool(form_parameters.get("extensible", True)),
        )
    return registry


def _enriched_policy_integrity_constraints(
    world: ArtifactStore,
    constraints: Sequence[IntegrityConstraint],
) -> tuple[IntegrityConstraint, ...]:
    concept_ids = sorted(_integrity_constraint_concept_ids(constraints))
    cel_registry = _cel_registry_for_concepts(world, concept_ids)
    enriched: list[IntegrityConstraint] = []
    for constraint in constraints:
        metadata = dict(constraint.metadata)
        if constraint.kind == IntegrityConstraintKind.CEL and "registry" not in metadata:
            metadata["registry"] = cel_registry
        enriched.append(
            IntegrityConstraint(
                kind=constraint.kind,
                concept_ids=constraint.concept_ids,
                metadata=metadata,
                cel=constraint.cel,
                description=constraint.description,
            )
        )
    return tuple(enriched)


def _build_global_ic_merge_problem(
    active_claim_rows: Sequence[Mapping[str, object]],
    target_concept_id: str,
    *,
    world: ArtifactStore,
    policy: RenderPolicy | None,
) -> ICMergeProblem:
    branch_weights = None if policy is None else policy.branch_weights
    merge_operator = (
        policy.merge_operator
        if policy is not None
        else MergeOperator.SIGMA
    )
    explicit_constraints = (
        tuple()
        if policy is None
        else _enriched_policy_integrity_constraints(world, policy.integrity_constraints)
    )
    concept_ids = {
        _claim_concept_id(claim)
        for claim in active_claim_rows
    }
    concept_ids.add(target_concept_id)
    concept_ids.update(_integrity_constraint_concept_ids(explicit_constraints))

    grouped: dict[str, dict[str, object]] = {}
    for claim in active_claim_rows:
        claim_id = _claim_id(claim)
        concept_id = _claim_concept_id(claim)
        branch = claim.get("branch")
        source_id = branch if isinstance(branch, str) and branch else claim_id
        per_source = grouped.setdefault(source_id, {})
        if concept_id in per_source:
            raise ValueError(
                f"source '{source_id}' has multiple active claims for concept '{concept_id}'"
            )
        per_source[concept_id] = claim

    sources: list[MergeSource] = []
    for source_id, concept_claims in grouped.items():
        sample_claim = next(iter(concept_claims.values()))
        branch = sample_claim.get("branch")
        weight = 1.0
        if branch_weights is not None and isinstance(branch, str) and branch:
            weight = float(branch_weights.get(branch, 1.0))
        sources.append(
            MergeSource(
                source_id=source_id,
                assignment=MergeAssignment(
                    values={
                        concept_id: _claim_value(claim)
                        for concept_id, claim in concept_claims.items()
                    }
                ),
                weight=weight,
            )
        )

    automatic_constraints: list[IntegrityConstraint] = []
    for concept_id in sorted(concept_ids):
        automatic_constraints.extend(_concept_integrity_constraints(world, concept_id))

    return ICMergeProblem(
        concept_ids=tuple(sorted(concept_ids)),
        sources=tuple(sources),
        constraints=tuple(automatic_constraints) + explicit_constraints,
        operator=merge_operator,
    )


def _claim_concept_id(claim: Mapping[str, object]) -> str:
    concept_id = claim.get("concept_id")
    if not isinstance(concept_id, str) or not concept_id:
        raise KeyError("resolution requires each claim to have a non-empty string concept_id")
    return concept_id


def _resolve_ic_merge(
    target_claim_rows: Sequence[Mapping[str, object]],
    active_claim_rows: Sequence[Mapping[str, object]],
    concept_id: str,
    *,
    world: ArtifactStore,
    policy: RenderPolicy | None = None,
) -> tuple[str | None, str | None]:
    from propstore.repo.ic_merge import solve_ic_merge

    if world is None:
        return None, "ic_merge strategy requires an explicit artifact store"

    filtered_rows = _filtered_ic_merge_claim_rows(active_claim_rows, policy)
    if not filtered_rows:
        return None, "no IC-merge sources after branch filter"
    try:
        problem = _build_global_ic_merge_problem(
            filtered_rows,
            concept_id,
            world=world,
            policy=policy,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)

    result = solve_ic_merge(problem)
    if not result.winners:
        return None, result.reason

    target_values = {
        winner.value_for(concept_id)
        for winner in result.winners
    }
    if len(target_values) != 1:
        return None, f"{len(result.winners)} IC-merge assignments disagree on target value"

    winning_value = next(iter(target_values))
    matching_claims = [
        claim
        for claim in target_claim_rows
        if _claim_value(claim) == winning_value
    ]
    if len(matching_claims) != 1:
        return None, (
            f"merged target value represented by {len(matching_claims)} active claims"
        )

    return _claim_id(matching_claims[0]), (
        f"global IC merge ({problem.operator}) winner satisfies {len(problem.constraints)} constraints across {len(problem.concept_ids)} concepts"
    )


def _resolve_claim_graph_argumentation(
    target_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
    active_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
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
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    from propstore.core.analyzers import (
        analyze_claim_graph,
        shared_analyzer_input_from_active_graph,
        shared_analyzer_input_from_store,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data"

    active_views = tuple(_coerce_resolution_claim(claim) for claim in active_claims)
    target_views = tuple(_coerce_resolution_claim(claim) for claim in target_claims)
    active_ids = {c.id for c in active_views}
    target_ids = {c.id for c in target_views}
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

    survivors = frozenset(projection.survivor_claim_ids if projection is not None else ())
    witness_claims = frozenset(projection.witness_claim_ids if projection is not None else ())

    if len(survivors) == 0:
        if len(result.extensions) > 1:
            if witness_claims:
                return None, f"no skeptically accepted claim in {normalized_semantics.value} extensions"
            return None, f"all target claims absent from every {normalized_semantics.value} extension"
        return None, "all claims defeated"
    if len(survivors) == 1:
        winner = next(iter(survivors))
        return winner, f"sole survivor in {normalized_semantics.value} extension"

    return None, f"{len(survivors)} claims survive in {normalized_semantics.value} extension"


def _resolve_structured_argumentation(
    target_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
    active_claim_rows: list[dict],
    view: BeliefSpace,
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    link: str = "last",
) -> tuple[str | None, str | None]:
    """Resolve via the structured projection compatibility wrapper."""
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.ASPIC,
        semantics,
    )
    from propstore.structured_argument import (
        build_structured_projection,
        compute_structured_justified_arguments,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data"

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    if isinstance(view, ClaimSupportView):
        for claim in active_claim_rows:
            claim_id = _claim_id(claim)
            support_metadata[claim_id] = view.claim_support(claim)

    projection = build_structured_projection(
        world,
        active_claim_rows,
        support_metadata=support_metadata,
        comparison=comparison,
        link=link,
        active_graph=view._active_graph if isinstance(view, HasActiveGraph) else None,
    )
    result = compute_structured_justified_arguments(
        projection,
        semantics=normalized_semantics,
        backend=ReasoningBackend.ASPIC,
    )

    target_views = tuple(_coerce_resolution_claim(claim) for claim in target_claims)
    target_arg_ids = frozenset(
        arg_id
        for claim in target_views
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
        projection.argument_to_claim_id[arg_id]
        for arg_id in survivor_args
    }
    if len(survivor_claims) == 0:
        return None, "all ASPIC+ arguments defeated"
    if len(survivor_claims) == 1:
        winner = next(iter(survivor_claims))
        return winner, f"sole ASPIC+ survivor in {normalized_semantics.value} extension"

    return None, f"{len(survivor_claims)} claims survive in {normalized_semantics.value} ASPIC+ projection"


def _resolve_aspic_argumentation(
    target_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
    active_claim_rows: list[dict],
    view: BeliefSpace,
    world: ArtifactStore,
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    link: str = "last",
) -> tuple[str | None, str | None]:
    """Resolve via the canonical ASPIC+ backend."""
    return _resolve_structured_argumentation(
        target_claims,
        active_claim_rows,
        view,
        world,
        semantics=semantics,
        comparison=comparison,
        link=link,
    )


def _resolve_praf(
    target_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
    active_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
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
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.PRAF,
        semantics,
    )

    if not world.has_table("relation_edge"):
        return None, "no stance data", None

    target_views = tuple(_coerce_resolution_claim(claim) for claim in target_claims)
    active_views = tuple(_coerce_resolution_claim(claim) for claim in active_claims)
    active_ids = {c.id for c in active_views}
    target_ids = {c.id for c in target_views}

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
        semantics=normalized_semantics,
        strategy=strategy,
        query_kind="argument_acceptance",
        inference_mode="credulous",
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
        claim_lookup = {c.id: c for c in target_views}
        decision_values: dict[str, float | None] = {}
        for cid in best_claims:
            claim = claim_lookup.get(cid)
            decision_values[cid] = apply_decision_criterion(
                None if claim is None else claim.opinion_belief,
                None if claim is None else claim.opinion_disbelief,
                None if claim is None else claim.opinion_uncertainty,
                None if claim is None else claim.opinion_base_rate,
                None if claim is None else claim.confidence,
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
    target_claims: Sequence[_ResolutionClaimView | Mapping[str, object]],
    view: BeliefSpace,
) -> tuple[str | None, str | None]:
    """Resolve by ATMS-supported status over the active belief space."""
    if not isinstance(view, HasATMSEngine):
        raise NotImplementedError("ATMS backend requires a bound world with an ATMS engine")

    engine = view.atms_engine()
    target_ids = {claim.id for claim in (_coerce_resolution_claim(row) for row in target_claims)}
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
    link: str | None = None,
    policy: RenderPolicy | None = None,
) -> ResolvedResult:
    """Apply a resolution strategy to a conflicted concept."""
    vr = view.value_of(concept_id)

    if vr.status == "no_claims":
        return ResolvedResult(concept_id=concept_id, status=ValueStatus.NO_CLAIMS)

    if vr.status == "determined":
        determined_claim = (
            _resolution_claim_view(vr.claims[0])
            if vr.claims
            else None
        )
        value = None if determined_claim is None else determined_claim.value
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
            concept_id=concept_id, status=ValueStatus.CONFLICTED,
            claims=vr.claims, reason="no resolution strategy configured",
        )

    # Conflicted — apply strategy
    active = vr.claims
    active_views = tuple(_resolution_claim_view(claim) for claim in active)
    active_claim_rows = list(view.active_claims())
    active_claim_views = tuple(_resolution_claim_view(claim) for claim in active_claim_rows)
    winner_id: str | None = None
    reason: str | None = None
    _acceptance_probs: dict[str, float] | None = None
    active_graph = view._active_graph if isinstance(view, HasActiveGraph) else None

    if strategy == ResolutionStrategy.OVERRIDE:
        override_id = (overrides or {}).get(concept_id)
        if override_id is None:
            return ResolvedResult(
                concept_id=concept_id, status=ValueStatus.CONFLICTED,
                claims=active, reason="no override specified",
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

    elif strategy == ResolutionStrategy.IC_MERGE:
        if world is None:
            return ResolvedResult(
                concept_id=concept_id,
                status=ValueStatus.CONFLICTED,
                claims=active,
                strategy=strategy.value,
                reason="ic_merge strategy requires an explicit artifact store",
            )
        winner_id, reason = _resolve_ic_merge(
            active,
            active_claim_rows,
            concept_id,
            world=world,
            policy=policy,
        )

    elif strategy == ResolutionStrategy.ARGUMENTATION:
        if world is None:
            return ResolvedResult(
                concept_id=concept_id, status=ValueStatus.CONFLICTED,
                claims=active, reason="argumentation strategy requires an explicit artifact store",
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
                active_claim_rows,
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
            concept_id=concept_id, status=ValueStatus.CONFLICTED,
            claims=active, strategy=strategy.value, reason=reason,
            acceptance_probs=_acceptance_probs,
        )

    winning_claim = next((claim for claim in active_views if claim.id == winner_id), None)
    value = None if winning_claim is None else winning_claim.value
    return ResolvedResult(
        concept_id=concept_id, status=ValueStatus.RESOLVED,
        value=value, claims=active,
        winning_claim_id=winner_id,
        strategy=strategy.value, reason=reason,
        acceptance_probs=_acceptance_probs,
    )
