"""Intervention-ranked fragility orchestrator."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from propstore.core.environment import Environment
from propstore.core.id_types import to_context_id
from propstore.fragility_contributors import (
    build_bound_bridge_inputs,
    collect_assumption_interventions,
    collect_bridge_undercut_interventions,
    collect_conflict_interventions,
    collect_ground_fact_interventions,
    collect_grounded_rule_interventions,
    collect_missing_measurement_interventions,
    derive_scored_concepts,
)
from propstore.fragility_scoring import (
    FragilityWarning,
    combine_fragility,
    detect_interactions,
    imps_rev,
    opinion_sensitivity,
    score_conflict,
    support_derivative_fragility,
    weighted_epistemic_score,
)
from propstore.fragility_types import (
    AssumptionTarget,
    BridgeUndercutTarget,
    ConflictTarget,
    FragilityInteraction,
    FragilityReport,
    FragilityWorld,
    GroundFactTarget,
    GroundedRuleTarget,
    InteractionType,
    InterventionFamily,
    InterventionKind,
    InterventionProvenance,
    InterventionTarget,
    MissingMeasurementTarget,
    RankedIntervention,
    RankingPolicy,
)
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.world.types import QueryableAssumption

if TYPE_CHECKING:
    from propstore.world import WorldModel


@dataclass(frozen=True)
class FragilityRequest:
    bindings: Mapping[str, str]
    context_id: str | None = None
    concept_id: str | None = None
    top_k: int = 20
    include_atms: bool = True
    include_discovery: bool = True
    include_conflict: bool = True
    include_grounding: bool = True
    include_bridge: bool = True
    ranking_policy: RankingPolicy | str = RankingPolicy.HEURISTIC_ROI


def query_fragility(
    world: WorldModel,
    request: FragilityRequest,
) -> FragilityReport:
    bound = world.bind(
        Environment(
            bindings=dict(request.bindings),
            context_id=(
                None
                if request.context_id is None
                else to_context_id(request.context_id)
            ),
        )
    )
    return rank_fragility(
        bound,
        concept_id=request.concept_id,
        top_k=request.top_k,
        include_atms=request.include_atms,
        include_discovery=request.include_discovery,
        include_conflict=request.include_conflict,
        include_grounding=request.include_grounding,
        include_bridge=request.include_bridge,
        ranking_policy=RankingPolicy(request.ranking_policy),
    )


def _apply_ranking_policy(
    interventions: Sequence[RankedIntervention],
    ranking_policy: RankingPolicy,
) -> tuple[RankedIntervention, ...]:
    def _retag(
        ordered: Sequence[RankedIntervention],
    ) -> tuple[RankedIntervention, ...]:
        return tuple(
            replace(item, ranking_policy=ranking_policy)
            for item in ordered
        )

    if ranking_policy is RankingPolicy.HEURISTIC_ROI:
        return _retag(
            sorted(
                interventions,
                key=lambda ranked: (
                    ranked.roi,
                    ranked.local_fragility,
                    ranked.target.intervention_id,
                ),
                reverse=True,
            )
        )
    if ranking_policy is RankingPolicy.FAMILY_LOCAL_ONLY:
        return _retag(
            sorted(
                interventions,
                key=lambda ranked: (
                    ranked.target.family.value,
                    -ranked.local_fragility,
                    ranked.target.intervention_id,
                ),
            )
        )
    if ranking_policy is RankingPolicy.PARETO:
        nondominated: list[RankedIntervention] = []
        for candidate in interventions:
            dominated = False
            for other in interventions:
                if other is candidate:
                    continue
                if (
                    other.local_fragility >= candidate.local_fragility
                    and other.target.cost_tier <= candidate.target.cost_tier
                    and (
                        other.local_fragility > candidate.local_fragility
                        or other.target.cost_tier < candidate.target.cost_tier
                    )
                ):
                    dominated = True
                    break
            if not dominated:
                nondominated.append(candidate)
        return _retag(
            sorted(
                nondominated,
                key=lambda ranked: (
                    ranked.local_fragility,
                    -ranked.target.cost_tier,
                    ranked.target.intervention_id,
                ),
                reverse=True,
            )
        )
    raise ValueError(f"Unknown ranking policy: {ranking_policy!r}")


def rank_fragility(
    bound: FragilityWorld,
    *,
    concept_id: str | None = None,
    queryables: Sequence[QueryableAssumption] | None = None,
    top_k: int = 20,
    include_atms: bool = True,
    include_discovery: bool = True,
    include_conflict: bool = True,
    include_grounding: bool = True,
    include_bridge: bool = True,
    ranking_policy: RankingPolicy = RankingPolicy.HEURISTIC_ROI,
    atms_limit: int = 8,
) -> FragilityReport:
    concept_ids = [concept_id] if concept_id is not None else derive_scored_concepts(bound)
    interventions: list[RankedIntervention] = []

    if include_atms:
        interventions.extend(
            collect_assumption_interventions(
                bound,
                concept_ids,
                queryables,
                atms_limit=atms_limit,
            )
        )

    if include_discovery:
        interventions.extend(collect_missing_measurement_interventions(bound, concept_ids))

    if include_conflict:
        interventions.extend(collect_conflict_interventions(bound, concept_ids))

    bundle_getter = getattr(bound._store, "grounding_bundle", None)
    bundle = bundle_getter() if callable(bundle_getter) else GroundedRulesBundle.empty()

    if include_grounding:
        interventions.extend(collect_ground_fact_interventions(bundle))
        interventions.extend(collect_grounded_rule_interventions(bundle))

    if include_bridge:
        active_claims, justifications, stance_rows = build_bound_bridge_inputs(bound)
        interventions.extend(
            collect_bridge_undercut_interventions(
                bundle,
                active_claims,
                justifications,
                stance_rows,
            )
        )

    normalized_policy = RankingPolicy(ranking_policy)
    ranked = _apply_ranking_policy(interventions, normalized_policy)
    ranked = ranked[:top_k]
    world_fragility = (
        sum(item.local_fragility for item in ranked[: min(10, len(ranked))]) / min(10, len(ranked))
        if ranked
        else 0.0
    )
    interactions = detect_interactions(ranked, bound, top_k=min(top_k, 5), atms_limit=atms_limit)
    scope = f"subject:{concept_id}" if concept_id is not None else "all"
    return FragilityReport(
        interventions=ranked,
        world_fragility=world_fragility,
        analysis_scope=scope,
        interactions=interactions,
    )


__all__ = [
    "AssumptionTarget",
    "BridgeUndercutTarget",
    "ConflictTarget",
    "FragilityInteraction",
    "FragilityReport",
    "FragilityWarning",
    "FragilityWorld",
    "GroundFactTarget",
    "GroundedRuleTarget",
    "InteractionType",
    "InterventionFamily",
    "InterventionKind",
    "InterventionProvenance",
    "InterventionTarget",
    "MissingMeasurementTarget",
    "RankedIntervention",
    "RankingPolicy",
    "build_bound_bridge_inputs",
    "collect_assumption_interventions",
    "collect_bridge_undercut_interventions",
    "collect_conflict_interventions",
    "collect_ground_fact_interventions",
    "collect_grounded_rule_interventions",
    "collect_missing_measurement_interventions",
    "combine_fragility",
    "detect_interactions",
    "imps_rev",
    "opinion_sensitivity",
    "rank_fragility",
    "score_conflict",
    "support_derivative_fragility",
    "weighted_epistemic_score",
]
