"""Scoring and interaction helpers for fragility."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import replace
from itertools import combinations
from typing import TYPE_CHECKING

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
    from propstore.dung import ArgumentationFramework
    from propstore.opinion import Opinion


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
    from propstore.dung import ArgumentationFramework, grounded_extension

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
            assumption_id=payload.queryable_id,
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
        witnesses = stability.get("witnesses", [])
        singleton_by_qcel: dict[str, set[str]] = {}
        for witness in witnesses:
            q_cels = [str(item) for item in witness.get("queryable_cels", [])]
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
    qcel: str,
    target_queryables: dict[str, QueryableAssumption],
) -> str | None:
    for intervention_id, queryable in target_queryables.items():
        if queryable.cel == qcel:
            return intervention_id
    return None


_TOL = 1e-9


def _try_perturb(opinion: Opinion, delta_u: float, a: float) -> Opinion | None:
    from propstore.opinion import Opinion

    expectation = opinion.expectation()
    u_new = opinion.u + delta_u
    if u_new < _TOL or u_new > 1.0 - _TOL:
        return None
    b_new = expectation - a * u_new
    d_new = 1.0 - u_new - b_new
    if b_new < -_TOL or d_new < -_TOL:
        return None
    b_new = max(0.0, b_new)
    d_new = max(0.0, d_new)
    try:
        return Opinion(b_new, d_new, u_new, a)
    except ValueError:
        return None


def opinion_sensitivity(
    opinions: Sequence[Opinion],
    index: int,
    *,
    delta: float = 0.01,
) -> float | None:
    from propstore.opinion import wbf

    if len(opinions) < 2:
        return None
    for opinion in opinions:
        if opinion.u < _TOL:
            return None

    target = opinions[index]

    def _try_fuse(candidate: Opinion) -> float | None:
        mutable = list(opinions)
        mutable[index] = candidate
        try:
            return wbf(*mutable).expectation()
        except ValueError:
            return None

    current_delta = delta
    for _attempt in range(3):
        minus = _try_perturb(target, -current_delta, target.a)
        plus = _try_perturb(target, current_delta, target.a)
        if minus is not None and plus is not None:
            expectation_minus = _try_fuse(minus)
            expectation_plus = _try_fuse(plus)
            if expectation_minus is not None and expectation_plus is not None:
                return abs(expectation_plus - expectation_minus) / (2.0 * current_delta)
        if plus is not None:
            expectation_base = _try_fuse(target)
            expectation_plus = _try_fuse(plus)
            if expectation_base is not None and expectation_plus is not None:
                return abs(expectation_plus - expectation_base) / current_delta
        if minus is not None:
            expectation_base = _try_fuse(target)
            expectation_minus = _try_fuse(minus)
            if expectation_base is not None and expectation_minus is not None:
                return abs(expectation_base - expectation_minus) / current_delta
        current_delta /= 2.0
    return None


def imps_rev(
    framework: ArgumentationFramework,
    supports: dict[tuple[str, str], float],
    base_scores: dict[str, float],
    attack: tuple[str, str],
) -> float:
    from propstore.dung import ArgumentationFramework as AF
    from propstore.opinion import Opinion
    from propstore.praf import ProbabilisticAF
    from propstore.praf.dfquad import compute_dfquad_strengths

    if attack not in framework.defeats:
        return 0.0
    p_args = {argument: Opinion.dogmatic_true() for argument in framework.arguments}
    p_defeats = {defeat: Opinion.dogmatic_true() for defeat in framework.defeats}
    praf = ProbabilisticAF(framework=framework, p_args=p_args, p_defeats=p_defeats)
    strengths_full = compute_dfquad_strengths(praf, supports, base_scores=base_scores)

    reduced_framework = AF(
        arguments=framework.arguments,
        defeats=frozenset(defeat for defeat in framework.defeats if defeat != attack),
    )
    reduced_p_defeats = {key: value for key, value in p_defeats.items() if key != attack}
    reduced_praf = ProbabilisticAF(
        framework=reduced_framework,
        p_args=p_args,
        p_defeats=reduced_p_defeats,
    )
    strengths_reduced = compute_dfquad_strengths(
        reduced_praf,
        supports,
        base_scores=base_scores,
    )
    return strengths_reduced[attack[1]] - strengths_full[attack[1]]
