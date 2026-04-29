from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum
from typing import overload

from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import Formula, World
from propstore.core.anytime import EnumerationExceeded


class ICMergeOperator(StrEnum):
    SIGMA = "sigma"
    GMAX = "gmax"


class ICMergeProfileMemberInconsistent(ValueError):
    """Raised when an IC profile contains an unsatisfiable formula."""

    def __init__(self, formula: Formula) -> None:
        self.formula = formula
        super().__init__("IC merge profile member has no models")

    def __str__(self) -> str:
        return "IC merge profile member has no models"


@dataclass(frozen=True, slots=True)
class ICMergeOutcome:
    belief_set: BeliefSet
    scored_worlds: tuple[tuple[World, float | tuple[float, ...]], ...]


@dataclass(slots=True)
class _DistanceFormulaCacheEntry:
    formula: Formula
    models: tuple[World, ...]
    distances: dict[World, float]


_DISTANCE_FORMULA_CACHE_MAX_SIZE = 128
_DISTANCE_FORMULA_CACHE: OrderedDict[
    tuple[object, frozenset[str]],
    _DistanceFormulaCacheEntry,
] = OrderedDict()


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
    _raise_for_unsatisfiable_profile_members(profile, signature)
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
    if operator == ICMergeOperator.SIGMA:
        return float(sum(distances))
    if operator == ICMergeOperator.GMAX:
        return tuple(sorted(distances, reverse=True))
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

    Konieczny and Pino Pérez 2002 IC merging repeatedly evaluates distances to
    the same profile formulas across candidate worlds; uncapped exact calls
    therefore memoize each formula's model set and per-world distances.
    """

    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative")

    if max_candidates is None:
        entry = _distance_formula_cache_entry(formula, signature)
        cached_distance = entry.distances.get(world)
        if cached_distance is not None:
            return cached_distance
        if not entry.models:
            entry.distances[world] = math.inf
            return math.inf
        distance = float(min(_hamming(world, model) for model in entry.models))
        entry.distances[world] = distance
        return distance

    best_distance: int | None = None
    examined = 0
    for candidate in BeliefSet.all_worlds(signature):
        if examined >= max_candidates:
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


def _distance_formula_cache_entry(
    formula: Formula,
    signature: frozenset[str],
) -> _DistanceFormulaCacheEntry:
    key = (formula, signature)
    cached = _DISTANCE_FORMULA_CACHE.get(key)
    if cached is not None:
        _DISTANCE_FORMULA_CACHE.move_to_end(key)
        return cached

    models = tuple(
        candidate
        for candidate in BeliefSet.all_worlds(signature)
        if formula.evaluate(candidate)
    )
    entry = _DistanceFormulaCacheEntry(
        formula=formula,
        models=models,
        distances={},
    )
    _DISTANCE_FORMULA_CACHE[key] = entry
    _DISTANCE_FORMULA_CACHE.move_to_end(key)
    while len(_DISTANCE_FORMULA_CACHE) > _DISTANCE_FORMULA_CACHE_MAX_SIZE:
        _DISTANCE_FORMULA_CACHE.popitem(last=False)
    return entry


def _raise_for_unsatisfiable_profile_members(
    profile: tuple[Formula, ...],
    signature: frozenset[str],
) -> None:
    for formula in profile:
        if not _distance_formula_cache_entry(formula, signature).models:
            raise ICMergeProfileMemberInconsistent(formula)


def _hamming(left: World, right: World) -> int:
    return len(left.symmetric_difference(right))


def _score_key(score: float | tuple[float, ...]) -> tuple[float, ...]:
    if isinstance(score, tuple):
        return tuple(float(item) for item in score)
    return (score,)
