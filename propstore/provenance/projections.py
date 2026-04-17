"""Projection homomorphisms for provenance polynomials."""

from __future__ import annotations

from collections.abc import Container, Mapping
from dataclasses import dataclass
from math import inf

from propstore.core.id_types import AssumptionId, ContextId, to_assumption_id, to_context_id
from propstore.provenance.homomorphism import evaluate
from propstore.provenance.polynomial import ProvenancePolynomial
from propstore.provenance.variables import SourceVariableId


@dataclass(frozen=True)
class WhySupport:
    assumption_ids: tuple[AssumptionId, ...] = ()
    context_ids: tuple[ContextId, ...] = ()
    other_variables: tuple[SourceVariableId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assumption_ids",
            tuple(sorted(dict.fromkeys(to_assumption_id(item) for item in self.assumption_ids))),
        )
        object.__setattr__(
            self,
            "context_ids",
            tuple(sorted(dict.fromkeys(to_context_id(item) for item in self.context_ids))),
        )
        object.__setattr__(
            self,
            "other_variables",
            tuple(sorted(dict.fromkeys(SourceVariableId(str(item)) for item in self.other_variables))),
        )

    def union(self, other: WhySupport) -> WhySupport:
        return WhySupport(
            self.assumption_ids + other.assumption_ids,
            self.context_ids + other.context_ids,
            self.other_variables + other.other_variables,
        )

    def subsumes(self, other: WhySupport) -> bool:
        return (
            set(self.assumption_ids).issubset(other.assumption_ids)
            and set(self.context_ids).issubset(other.context_ids)
            and set(self.other_variables).issubset(other.other_variables)
        )


def boolean_presence(
    poly: ProvenancePolynomial,
    trusted: Container[SourceVariableId],
) -> bool:
    for term in poly.terms:
        if all(power.variable in trusted for power in term.powers):
            return True
    return False


def derivation_count(poly: ProvenancePolynomial) -> int:
    return sum(term.coefficient for term in poly.terms)


def why_provenance(
    poly: ProvenancePolynomial,
    *,
    assumption_variables: Mapping[SourceVariableId, AssumptionId] | None = None,
    context_variables: Mapping[SourceVariableId, ContextId] | None = None,
) -> tuple[WhySupport, ...]:
    assumption_variables = assumption_variables or {}
    context_variables = context_variables or {}
    supports: list[WhySupport] = []
    for term in poly.terms:
        assumptions: list[AssumptionId] = []
        contexts: list[ContextId] = []
        others: list[SourceVariableId] = []
        for variable in term.squarefree_support():
            if variable in assumption_variables:
                assumptions.append(assumption_variables[variable])
            elif variable in context_variables:
                contexts.append(context_variables[variable])
            else:
                others.append(variable)
        supports.append(WhySupport(tuple(assumptions), tuple(contexts), tuple(others)))
    return normalize_why_supports(supports)


def normalize_why_supports(supports: list[WhySupport]) -> tuple[WhySupport, ...]:
    unique = {
        (support.assumption_ids, support.context_ids, support.other_variables): support
        for support in supports
    }
    ordered = sorted(
        unique.values(),
        key=lambda support: (
            len(support.assumption_ids) + len(support.context_ids) + len(support.other_variables),
            support.assumption_ids,
            support.context_ids,
            support.other_variables,
        ),
    )
    minimal: list[WhySupport] = []
    for candidate in ordered:
        if any(existing.subsumes(candidate) for existing in minimal):
            continue
        minimal.append(candidate)
    return tuple(minimal)


class _TropicalCostHomomorphism:
    """Min-plus cost projection; these floats are costs, not confidence values."""

    def __init__(self, costs: Mapping[SourceVariableId, float]) -> None:
        self._costs = costs

    @property
    def zero(self) -> float:
        return inf

    @property
    def one(self) -> float:
        return 0.0

    def add(self, left: float, right: float) -> float:
        return min(left, right)

    def mul(self, left: float, right: float) -> float:
        return left + right

    def variable(self, variable: SourceVariableId) -> float:
        return float(self._costs.get(variable, inf))


def tropical_cost(
    poly: ProvenancePolynomial,
    costs: Mapping[SourceVariableId, float],
) -> float:
    """Return the preferred derivation cost, not a probability or confidence."""

    return evaluate(poly, _TropicalCostHomomorphism(costs))
