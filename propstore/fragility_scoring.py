"""Scoring and interaction helpers for fragility."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from itertools import combinations
from typing import TYPE_CHECKING

from propstore.cel_types import CelExpr
from propstore.fragility_types import (
    AssumptionTarget,
    FragilityInteraction,
    FragilityWorld,
    InteractionType,
    InterventionKind,
    RankedIntervention,
)
from propstore.core.id_types import QueryableId
from propstore.provenance import (
    ProvenanceNogood,
    ProvenancePolynomial,
    SourceVariableId,
    derivation_count,
    live,
    partial_derivative,
)
from propstore.world.types import QueryableAssumption

if TYPE_CHECKING:
    from argumentation.dung import ArgumentationFramework
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
    from argumentation.dung import ArgumentationFramework, grounded_extension

    if semantics != "grounded":
        raise ValueError(f"Unsupported semantics: {semantics!r}")
    if not framework.arguments:
        return 0.0

    total = len(framework.arguments)
    current = grounded_extension(framework)

    def _remove(arg_id: str) -> frozenset[str]:
        reduced = ArgumentationFramework(
            arguments=frozenset(
                argument for argument in framework.arguments if argument != arg_id
            ),
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
            witness_weight = sum(
                probability_weights[index] for index in witness_indices
            )
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


def _intervention_for_qcel(
    qcel: str | CelExpr,
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
    from propstore.opinion import Opinion

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
            return Opinion.wbf(*mutable).expectation()
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
    *,
    p_args: dict[str, Opinion],
    p_defeats: dict[tuple[str, str], Opinion],
) -> float:
    from argumentation.dung import ArgumentationFramework as AF
    from argumentation.dfquad import dfquad_strengths
    from argumentation.gradual import WeightedBipolarGraph

    if attack not in framework.defeats:
        return 0.0

    missing_args = sorted(
        argument for argument in framework.arguments if argument not in p_args
    )
    missing_defeats = sorted(
        defeat for defeat in framework.defeats if defeat not in p_defeats
    )
    if missing_args or missing_defeats:
        raise ValueError(
            "imps_rev requires explicit probabilistic inputs for every argument "
            f"and defeat; missing_args={missing_args}, missing_defeats={missing_defeats}"
        )
    unprovenanced_args = sorted(
        argument for argument, opinion in p_args.items() if opinion.provenance is None
    )
    unprovenanced_defeats = sorted(
        defeat for defeat, opinion in p_defeats.items() if opinion.provenance is None
    )
    if unprovenanced_args or unprovenanced_defeats:
        raise ValueError(
            "imps_rev requires provenance-bearing opinions; "
            f"unprovenanced_args={unprovenanced_args}, "
            f"unprovenanced_defeats={unprovenanced_defeats}"
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
