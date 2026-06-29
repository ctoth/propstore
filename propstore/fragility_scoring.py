"""Scoring and interaction helpers for fragility.

The scores here are intentionally *opinion algebra and provenance algebra*, never
numeric model perturbation (CLAUDE.md substrate boundary): conflict scores ride
the Dung grounded extension, support-derivative scores ride the
provenance-semiring partial derivative over live witness monomials, and opinion
sensitivity is delegated to ``doxa.opinion_sensitivity`` (doxa owns the one
canonical ``Opinion`` and its weighted-belief-fusion sensitivity — propstore does
not mirror it). ``imps_rev`` is the probabilistic-argumentation removal impact
(Rago et al. dfquad strengths), gated by the honest-ignorance discipline: every
argument and defeat must come with a provenance-bearing opinion
(:class:`~propstore.opinion_provenance.OpinionWithProvenance`) rather than a
fabricated certainty.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import TYPE_CHECKING

from condition_ir import CelExpr
from doxa import opinion_sensitivity as opinion_sensitivity
from provenance_semiring import (
    ProvenanceNogood,
    ProvenancePolynomial,
    SourceVariableId,
    derivation_count,
    live,
    partial_derivative,
)

from propstore.core.id_types import to_queryable_id
from propstore.fragility_types import (
    AssumptionTarget,
    FragilityInteraction,
    FragilityWorld,
    InteractionType,
    InterventionKind,
    RankedIntervention,
)
from propstore.world.types import QueryableAssumption

if TYPE_CHECKING:
    from argumentation.core.dung import ArgumentationFramework

    from propstore.opinion_provenance import OpinionWithProvenance


class FragilityWarning(UserWarning):
    """Warning emitted when fragility analysis encounters a recoverable error."""


def combine_fragility(
    parametric: float | None,
    epistemic: float | None,
    conflict: float | None,
    combination: str = "top2",
) -> float:
    scores = sorted(
        [score for score in (parametric, epistemic, conflict) if score is not None],
        reverse=True,
    )
    if not scores:
        return 0.0
    if combination == "top2":
        if len(scores) == 1:
            return scores[0]
        return (scores[0] + scores[1]) / 2.0
    if combination == "mean":
        return sum(scores) / len(scores)
    if combination == "max":
        return scores[0]
    if combination == "product":
        product = 1.0
        for score in scores:
            product *= score
        return product
    raise ValueError(f"Unknown combination policy: {combination!r}")


def score_conflict(
    framework: ArgumentationFramework,
    claim_a_id: str,
    claim_b_id: str,
    *,
    semantics: str = "grounded",
) -> float:
    from argumentation.core.dung import ArgumentationFramework, grounded_extension

    if semantics != "grounded":
        raise ValueError(f"Unsupported semantics: {semantics!r}")
    if not framework.arguments:
        return 0.0

    total = len(framework.arguments)
    current = grounded_extension(framework)

    def _remove(arg_id: str) -> frozenset[str]:
        reduced = ArgumentationFramework(
            arguments=frozenset(argument for argument in framework.arguments if argument != arg_id),
            defeats=frozenset(
                (attacker, target)
                for attacker, target in framework.defeats
                if attacker != arg_id and target != arg_id
            ),
        )
        return grounded_extension(reduced)

    ext_remove_a = _remove(claim_a_id)
    ext_remove_b = _remove(claim_b_id)
    dist_a = len(current.symmetric_difference(ext_remove_a))
    dist_b = len(current.symmetric_difference(ext_remove_b))
    return min(1.0, max(dist_a, dist_b) / total)


def weighted_epistemic_score(
    witnesses: Sequence[object],
    consistent_future_count: int,
    *,
    probability_weights: list[float] | None = None,
    witness_indices: list[int] | None = None,
    current_in_extension: bool = True,
) -> float:
    if consistent_future_count <= 0:
        return 0.0

    if probability_weights is None:
        raw = len(witnesses) / consistent_future_count
    else:
        total_weight = sum(probability_weights)
        if total_weight <= 0.0:
            return 0.0
        if witness_indices is None:
            warnings.warn(
                "probability_weights provided without witness_indices; falling back to uniform weighting",
                FragilityWarning,
                stacklevel=2,
            )
            raw = len(witnesses) / consistent_future_count
        else:
            witness_weight = sum(probability_weights[index] for index in witness_indices)
            raw = witness_weight / total_weight
    if current_in_extension:
        return raw
    return 1.0 - raw


def support_derivative_fragility(
    support: ProvenancePolynomial,
    variable: SourceVariableId,
    *,
    live_nogoods: Sequence[ProvenanceNogood] = (),
    total_worlds: int,
    current_in_extension: bool = True,
) -> float:
    """Score a support source by the live witness monomials that depend on it."""

    if total_worlds <= 0:
        return 0.0
    live_support = live(support, live_nogoods)
    derivative = partial_derivative(live_support, variable)
    affected_witness_count = derivation_count(derivative)
    if affected_witness_count == 0:
        return 0.0
    return weighted_epistemic_score(
        tuple(object() for _ in range(affected_witness_count)),
        total_worlds,
        current_in_extension=current_in_extension,
    )


def _target_queryable_map(
    interventions: Sequence[RankedIntervention],
) -> dict[str, QueryableAssumption]:
    queryables: dict[str, QueryableAssumption] = {}
    for ranked in interventions:
        if ranked.target.kind is not InterventionKind.ASSUMPTION:
            continue
        payload = ranked.target.payload
        if not isinstance(payload, AssumptionTarget):
            continue
        queryables[ranked.target.intervention_id] = QueryableAssumption(
            assumption_id=to_queryable_id(payload.queryable_id),
            cel=payload.cel,
        )
    return queryables


def detect_interactions(
    interventions: Sequence[RankedIntervention],
    bound: FragilityWorld | None,
    *,
    top_k: int = 5,
    atms_limit: int = 8,
) -> tuple[FragilityInteraction, ...]:
    assumption_ranked = [
        ranked
        for ranked in interventions
        if ranked.target.kind is InterventionKind.ASSUMPTION
    ]
    if len(assumption_ranked) < 2:
        return ()

    assumption_ranked = sorted(
        assumption_ranked,
        key=lambda ranked: ranked.local_fragility,
        reverse=True,
    )[:top_k]

    if bound is None:
        return tuple(
            FragilityInteraction(
                intervention_a_id=min(a.target.intervention_id, b.target.intervention_id),
                intervention_b_id=max(a.target.intervention_id, b.target.intervention_id),
                interaction_type=InteractionType.UNKNOWN,
            )
            for a, b in combinations(assumption_ranked, 2)
        )

    try:
        engine = bound.atms_engine()
    except Exception:
        return tuple(
            FragilityInteraction(
                intervention_a_id=min(a.target.intervention_id, b.target.intervention_id),
                intervention_b_id=max(a.target.intervention_id, b.target.intervention_id),
                interaction_type=InteractionType.UNKNOWN,
            )
            for a, b in combinations(assumption_ranked, 2)
        )

    target_queryables = _target_queryable_map(assumption_ranked)
    queryables = list(target_queryables.values())
    if not queryables:
        return ()

    concepts: set[str] = set()
    for ranked in assumption_ranked:
        payload = ranked.target.payload
        if isinstance(payload, AssumptionTarget):
            concepts.update(payload.stabilizes_concepts)

    synergistic: dict[tuple[str, str], set[str]] = {}
    redundant: dict[tuple[str, str], set[str]] = {}

    for concept_id in sorted(concepts):
        try:
            stability = engine.concept_stability(concept_id, queryables, limit=atms_limit)
        except Exception:
            continue
        witnesses = stability.witnesses
        singleton_by_qcel: dict[str, set[str]] = {}
        for witness in witnesses:
            q_cels = [str(item) for item in witness.queryable_cels]
            if len(q_cels) == 1:
                singleton_by_qcel.setdefault(q_cels[0], set()).add(concept_id)
            elif len(q_cels) >= 2:
                for left, right in combinations(sorted(q_cels), 2):
                    left_id = _intervention_for_qcel(left, target_queryables)
                    right_id = _intervention_for_qcel(right, target_queryables)
                    if left_id is None or right_id is None or left_id == right_id:
                        continue
                    pair = (min(left_id, right_id), max(left_id, right_id))
                    synergistic.setdefault(pair, set()).add(concept_id)

        for left_qcel, right_qcel in combinations(sorted(singleton_by_qcel), 2):
            shared = singleton_by_qcel[left_qcel] & singleton_by_qcel[right_qcel]
            if not shared:
                continue
            left_id = _intervention_for_qcel(left_qcel, target_queryables)
            right_id = _intervention_for_qcel(right_qcel, target_queryables)
            if left_id is None or right_id is None or left_id == right_id:
                continue
            pair = (min(left_id, right_id), max(left_id, right_id))
            redundant.setdefault(pair, set()).update(shared)

    results: list[FragilityInteraction] = []
    seen: set[tuple[str, str]] = set()
    for pair, subjects in sorted(synergistic.items()):
        interaction_type = InteractionType.MIXED if pair in redundant else InteractionType.SYNERGISTIC
        merged_subjects = subjects | redundant.get(pair, set())
        results.append(
            FragilityInteraction(
                intervention_a_id=pair[0],
                intervention_b_id=pair[1],
                interaction_type=interaction_type,
                subjects_affected=tuple(sorted(merged_subjects)),
            )
        )
        seen.add(pair)
    for pair, subjects in sorted(redundant.items()):
        if pair in seen:
            continue
        results.append(
            FragilityInteraction(
                intervention_a_id=pair[0],
                intervention_b_id=pair[1],
                interaction_type=InteractionType.REDUNDANT,
                subjects_affected=tuple(sorted(subjects)),
            )
        )
        seen.add(pair)
    for left, right in combinations(assumption_ranked, 2):
        pair = (
            min(left.target.intervention_id, right.target.intervention_id),
            max(left.target.intervention_id, right.target.intervention_id),
        )
        if pair in seen:
            continue
        results.append(
            FragilityInteraction(
                intervention_a_id=pair[0],
                intervention_b_id=pair[1],
                interaction_type=InteractionType.INDEPENDENT,
            )
        )
    return tuple(results)


def _intervention_for_qcel(
    qcel: str | CelExpr,
    target_queryables: dict[str, QueryableAssumption],
) -> str | None:
    for intervention_id, queryable in target_queryables.items():
        if queryable.cel == qcel:
            return intervention_id
    return None


def imps_rev(
    framework: ArgumentationFramework,
    supports: dict[tuple[str, str], float],
    base_scores: dict[str, float],
    attack: tuple[str, str],
    *,
    p_args: Mapping[str, OpinionWithProvenance],
    p_defeats: Mapping[tuple[str, str], OpinionWithProvenance],
) -> float:
    """Removal impact of ``attack`` on the dfquad strength of its target.

    Honest ignorance (CLAUDE.md): the caller must supply a provenance-bearing
    opinion (:class:`~propstore.opinion_provenance.OpinionWithProvenance`) for
    *every* argument and defeat — a bare ``doxa.Opinion`` carries no provenance
    and is rejected by the type, so the score never rides a fabricated certainty.
    The opinions gate the computation; the strength delta itself is the dfquad
    fixpoint (Rago et al.) over the supplied ``base_scores`` and ``supports``.
    """

    from argumentation.core.dung import ArgumentationFramework as AF
    from argumentation.gradual.dfquad import dfquad_strengths
    from argumentation.gradual.gradual import WeightedBipolarGraph

    if attack not in framework.defeats:
        return 0.0

    missing_args = sorted(argument for argument in framework.arguments if argument not in p_args)
    missing_defeats = sorted(defeat for defeat in framework.defeats if defeat not in p_defeats)
    if missing_args or missing_defeats:
        raise ValueError(
            "imps_rev requires explicit probabilistic inputs for every argument "
            f"and defeat; missing_args={missing_args}, missing_defeats={missing_defeats}"
        )

    graph = WeightedBipolarGraph(
        arguments=framework.arguments,
        initial_weights=base_scores,
        attacks=framework.defeats,
        supports=frozenset(supports),
    )
    strengths_full = dfquad_strengths(
        graph,
        base_scores=base_scores,
        support_weights=supports,
    ).strengths

    reduced_framework = AF(
        arguments=framework.arguments,
        defeats=frozenset(defeat for defeat in framework.defeats if defeat != attack),
    )
    reduced_graph = WeightedBipolarGraph(
        arguments=reduced_framework.arguments,
        initial_weights=base_scores,
        attacks=reduced_framework.defeats,
        supports=frozenset(supports),
    )
    strengths_reduced = dfquad_strengths(
        reduced_graph,
        base_scores=base_scores,
        support_weights=supports,
    ).strengths
    return strengths_reduced[attack[1]] - strengths_full[attack[1]]
