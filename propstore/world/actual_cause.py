"""Halpern 2015 modified-HP actual-cause evaluation."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations, product
from typing import Literal

from propstore.core.id_types import ConceptId, to_concept_id
from propstore.world.intervention import InterventionWorld
from propstore.world.scm import StructuralCausalModel, Value


ActualCauseCriterion = Literal["AC1", "AC2", "AC3", "AC1+AC2+AC3"]
EffectPredicate = Callable[[Mapping[str, Value]], bool]


class EnumerationExceeded(RuntimeError):
    """Raised when modified-HP witness search exceeds its configured budget."""

    def __init__(self, *, max_witnesses: int, examined: int) -> None:
        self.max_witnesses = max_witnesses
        self.examined = examined
        super().__init__(
            f"Actual-cause witness search examined {examined} candidates, "
            f"exceeding max_witnesses={max_witnesses}"
        )


@dataclass(frozen=True)
class ActualCauseWitness:
    w_variables: tuple[str, ...]
    w_values: dict[str, Value]
    x_prime: dict[str, Value]


@dataclass(frozen=True)
class ActualCauseVerdict:
    holds: bool
    criterion: ActualCauseCriterion
    witness: ActualCauseWitness | None = None
    actual_values: dict[str, Value] | None = None
    smaller_cause: dict[str, Value] | None = None


def actual_cause(
    world: InterventionWorld,
    effect: EffectPredicate,
    candidate_cause: Mapping[ConceptId | str, Value],
    *,
    max_witnesses: int = 2 ** 14,
) -> ActualCauseVerdict:
    """Evaluate modified-HP actual causality over a finite recursive SCM."""
    scm = world.scm
    cause = {
        to_concept_id(concept_id): value
        for concept_id, value in candidate_cause.items()
    }
    ac1_values = scm.evaluate()
    actual_values = _string_values(ac1_values)

    if not _matches(ac1_values, cause) or not effect(actual_values):
        return ActualCauseVerdict(
            holds=False,
            criterion="AC1",
            actual_values=actual_values,
        )

    witness = _find_ac2_witness(
        scm,
        effect,
        cause,
        actual_values=ac1_values,
        max_witnesses=max_witnesses,
    )
    if witness is None:
        return ActualCauseVerdict(
            holds=False,
            criterion="AC2",
            actual_values=actual_values,
        )

    smaller_cause = _minimality_counterexample(
        scm,
        effect,
        cause,
        max_witnesses=max_witnesses,
    )
    if smaller_cause is not None:
        return ActualCauseVerdict(
            holds=False,
            criterion="AC3",
            witness=witness,
            actual_values=actual_values,
            smaller_cause=_string_values(smaller_cause),
        )

    return ActualCauseVerdict(
        holds=True,
        criterion="AC1+AC2+AC3",
        witness=witness,
        actual_values=actual_values,
    )


def _find_ac2_witness(
    scm: StructuralCausalModel,
    effect: EffectPredicate,
    cause: Mapping[ConceptId, Value],
    *,
    actual_values: Mapping[ConceptId, Value],
    max_witnesses: int,
) -> ActualCauseWitness | None:
    rest = sorted(scm.endogenous - frozenset(cause))
    examined = 0
    for w_variables in _subsets(rest):
        w_values = {
            variable: actual_values[variable]
            for variable in w_variables
        }
        for x_prime in _alternative_assignments(scm, cause):
            examined += 1
            if examined > max_witnesses:
                raise EnumerationExceeded(
                    max_witnesses=max_witnesses,
                    examined=examined,
                )
            intervened = scm.intervene({**x_prime, **w_values})
            post_values = _string_values(intervened.evaluate())
            if not effect(post_values):
                return ActualCauseWitness(
                    w_variables=tuple(str(variable) for variable in w_variables),
                    w_values=_string_values(w_values),
                    x_prime=_string_values(x_prime),
                )
    return None


def _minimality_counterexample(
    scm: StructuralCausalModel,
    effect: EffectPredicate,
    cause: Mapping[ConceptId, Value],
    *,
    max_witnesses: int,
) -> dict[ConceptId, Value] | None:
    if len(cause) <= 1:
        return None
    items = sorted(cause.items())
    for size in range(1, len(items)):
        for subset_items in combinations(items, size):
            subset = dict(subset_items)
            actual_values = scm.evaluate()
            if not _matches(actual_values, subset):
                continue
            if not effect(_string_values(actual_values)):
                continue
            witness = _find_ac2_witness(
                scm,
                effect,
                subset,
                actual_values=actual_values,
                max_witnesses=max_witnesses,
            )
            if witness is not None:
                return subset
    return None


def _alternative_assignments(
    scm: StructuralCausalModel,
    cause: Mapping[ConceptId, Value],
) -> Iterable[dict[ConceptId, Value]]:
    names = sorted(cause)
    alternatives: list[list[Value]] = []
    for name in names:
        domain = tuple(value for value in scm.domain_for(name) if value != cause[name])
        if not domain:
            return
        alternatives.append(list(domain))
    for values in product(*alternatives):
        yield dict(zip(names, values))


def _subsets(values: list[ConceptId]) -> Iterable[tuple[ConceptId, ...]]:
    for size in range(len(values) + 1):
        yield from combinations(values, size)


def _matches(
    values: Mapping[ConceptId, Value],
    expected: Mapping[ConceptId, Value],
) -> bool:
    return all(values.get(name) == value for name, value in expected.items())


def _string_values(values: Mapping[ConceptId, Value]) -> dict[str, Value]:
    return {
        str(name): value
        for name, value in values.items()
    }
