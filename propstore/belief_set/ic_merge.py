from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import overload

from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import Formula, World
from propstore.core.anytime import EnumerationExceeded


class ICMergeOperator(StrEnum):
    SIGMA = "sigma"
    GMAX = "gmax"


@dataclass(frozen=True, slots=True)
class ICMergeOutcome:
    belief_set: BeliefSet
    scored_worlds: tuple[tuple[World, float | tuple[float, ...]], ...]


def merge_belief_profile(
    alphabet: frozenset[str],
    profile: tuple[Formula, ...],
    mu: Formula,
    *,
    operator: ICMergeOperator = ICMergeOperator.SIGMA,
) -> ICMergeOutcome:
    """Konieczny-Pino Pérez style finite model-theoretic IC merge."""
    signature = frozenset(alphabet) | mu.atoms()
    for formula in profile:
        signature |= formula.atoms()
    candidates = tuple(
        world
        for world in BeliefSet.all_worlds(signature)
        if mu.evaluate(world)
    )
    if not candidates:
        return ICMergeOutcome(
            belief_set=BeliefSet.contradiction(signature),
            scored_worlds=(),
        )
    scored = tuple(
        sorted(
            ((world, _score_world(world, profile, signature, operator)) for world in candidates),
            key=lambda item: (_score_key(item[1]), tuple(sorted(item[0]))),
        )
    )
    best_score = scored[0][1]
    winners = frozenset(world for world, score in scored if score == best_score)
    return ICMergeOutcome(
        belief_set=BeliefSet(signature, winners),
        scored_worlds=scored,
    )


def _score_world(
    world: World,
    profile: tuple[Formula, ...],
    signature: frozenset[str],
    operator: ICMergeOperator,
) -> float | tuple[float, ...]:
    distances = tuple(_distance_to_formula(world, formula, signature) for formula in profile)
    finite_distances = tuple(distance for distance in distances if not math.isinf(distance))
    if operator == ICMergeOperator.SIGMA:
        return float(sum(finite_distances))
    if operator == ICMergeOperator.GMAX:
        return tuple(sorted(finite_distances, reverse=True))
    raise ValueError(f"Unsupported IC merge operator: {operator}")


@overload
def _distance_to_formula(world: World, formula: Formula, signature: frozenset[str]) -> float: ...


@overload
def _distance_to_formula(
    world: World,
    formula: Formula,
    signature: frozenset[str],
    *,
    max_candidates: None,
) -> float: ...


@overload
def _distance_to_formula(
    world: World,
    formula: Formula,
    signature: frozenset[str],
    *,
    max_candidates: int,
) -> float | EnumerationExceeded: ...


def _distance_to_formula(
    world: World,
    formula: Formula,
    signature: frozenset[str],
    *,
    max_candidates: int | None = None,
) -> float | EnumerationExceeded:
    """Return finite Hamming distance with an anytime candidate ceiling.

    Zilberstein 1996 frames bounded exact search as an anytime computation:
    if the candidate-world scan is interrupted before exactness is proven, the
    unvisited model space is reported as vacuous rather than approximated.
    """

    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative")

    best_distance: int | None = None
    examined = 0
    for candidate in BeliefSet.all_worlds(signature):
        if max_candidates is not None and examined >= max_candidates:
            return EnumerationExceeded(
                partial_count=examined,
                max_candidates=max_candidates,
            )
        examined += 1
        if not formula.evaluate(candidate):
            continue
        distance = _hamming(world, candidate)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            if best_distance == 0:
                return 0.0
    if best_distance is None:
        return math.inf
    return float(best_distance)


def _hamming(left: World, right: World) -> int:
    return len(left.symmetric_difference(right))


def _score_key(score: float | tuple[float, ...]) -> tuple[float, ...]:
    if isinstance(score, tuple):
        return tuple(float(item) for item in score)
    return (score,)
