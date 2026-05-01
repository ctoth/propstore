"""Structural causal models for intervention and actual-cause queries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, TypeAlias

from propstore.core.graph_types import CompiledWorldGraph, ParameterizationEdge
from propstore.core.id_types import ConceptId, to_concept_id

Value: TypeAlias = Any


@dataclass(frozen=True)
class StructuralEquation:
    """An equation F_X determining one endogenous variable from its parents."""

    target: ConceptId | str
    parents: tuple[ConceptId | str, ...]
    evaluate: Callable[[Mapping[str, Value]], Value]
    provenance: object | None = None
    domain: tuple[Value, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", to_concept_id(self.target))
        object.__setattr__(
            self,
            "parents",
            tuple(to_concept_id(parent) for parent in self.parents),
        )

    @classmethod
    def constant(
        cls,
        target: ConceptId | str,
        value: Value,
        *,
        provenance: object | None = None,
        domain: tuple[Value, ...] = (),
    ) -> StructuralEquation:
        return cls(
            target=target,
            parents=(),
            evaluate=lambda _values, value=value: value,
            provenance=provenance,
            domain=domain,
        )


@dataclass(frozen=True)
class StructuralCausalModel:
    """Finite recursive SCM with deterministic structural equations."""

    exogenous: frozenset[ConceptId | str]
    endogenous: frozenset[ConceptId | str]
    equations: Mapping[ConceptId | str, StructuralEquation]
    exogenous_assignment: Mapping[ConceptId | str, Value]
    domains: Mapping[ConceptId | str, tuple[Value, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        equations = {
            to_concept_id(target): equation
            for target, equation in self.equations.items()
        }
        endogenous = frozenset(to_concept_id(value) for value in self.endogenous) | frozenset(equations)
        exogenous_assignment = {
            to_concept_id(name): value
            for name, value in self.exogenous_assignment.items()
        }
        exogenous = (
            frozenset(to_concept_id(value) for value in self.exogenous)
            | frozenset(exogenous_assignment)
        ) - endogenous
        domains = {
            to_concept_id(name): tuple(values)
            for name, values in self.domains.items()
        }
        for name, value in {**exogenous_assignment, **self._constant_values(equations)}.items():
            domain = domains.get(name, ())
            if value not in domain:
                domains[name] = (*domain, value)
        for equation in equations.values():
            if equation.domain:
                domain = domains.get(equation.target, ())
                domains[equation.target] = tuple(dict.fromkeys((*domain, *equation.domain)))
        object.__setattr__(self, "exogenous", exogenous)
        object.__setattr__(self, "endogenous", endogenous)
        object.__setattr__(self, "equations", equations)
        object.__setattr__(self, "exogenous_assignment", exogenous_assignment)
        object.__setattr__(self, "domains", domains)

    @staticmethod
    def _constant_values(
        equations: Mapping[ConceptId, StructuralEquation],
    ) -> dict[ConceptId, Value]:
        values: dict[ConceptId, Value] = {}
        for target, equation in equations.items():
            if equation.parents:
                continue
            try:
                values[target] = equation.evaluate({})
            except Exception:
                continue
        return values

    @classmethod
    def from_compiled_graph(
        cls,
        graph: CompiledWorldGraph,
        *,
        exogenous_assignment: Mapping[ConceptId | str, Value] | None = None,
    ) -> StructuralCausalModel:
        equations = {
            edge.output_concept_id: _structural_equation_from_edge(edge)
            for edge in graph.parameterizations
            if edge.sympy
        }
        endogenous = frozenset(edge.output_concept_id for edge in graph.parameterizations)
        parent_ids = frozenset(
            parent
            for edge in graph.parameterizations
            for parent in edge.input_concept_ids
        )
        return cls(
            exogenous=parent_ids - endogenous,
            endogenous=endogenous,
            equations=equations,
            exogenous_assignment=dict(exogenous_assignment or {}),
        )

    def intervene(
        self,
        assignment: Mapping[ConceptId | str, Value],
    ) -> StructuralCausalModel:
        normalized = {
            to_concept_id(name): value
            for name, value in assignment.items()
        }
        equations = dict(self.equations)
        exogenous_assignment = dict(self.exogenous_assignment)
        endogenous = set(self.endogenous)
        exogenous = set(self.exogenous)
        domains = dict(self.domains)
        for target, value in normalized.items():
            domain = domains.get(target, ())
            if value not in domain:
                domains[target] = (*domain, value)
            if target in equations or target in endogenous:
                equations[target] = StructuralEquation.constant(
                    target,
                    value,
                    provenance=("intervention", str(target)),
                    domain=domains.get(target, ()),
                )
                endogenous.add(target)
                exogenous.discard(target)
            else:
                exogenous_assignment[target] = value
                exogenous.add(target)
        return StructuralCausalModel(
            exogenous=frozenset(exogenous),
            endogenous=frozenset(endogenous),
            equations=equations,
            exogenous_assignment=exogenous_assignment,
            domains=domains,
        )

    def evaluate(self) -> dict[ConceptId, Value]:
        values: dict[ConceptId, Value] = dict(self.exogenous_assignment)
        visiting: set[ConceptId] = set()

        def resolve(name: ConceptId) -> Value:
            if name in values:
                return values[name]
            equation = self.equations.get(name)
            if equation is None:
                raise ValueError(f"No value or structural equation for {name!r}")
            if name in visiting:
                raise ValueError(f"Cyclic structural equation dependency at {name!r}")
            visiting.add(name)
            try:
                for parent in equation.parents:
                    resolve(parent)
                value = equation.evaluate({str(key): item for key, item in values.items()})
                values[name] = value
                return value
            finally:
                visiting.discard(name)

        for name in sorted(self.endogenous):
            resolve(name)
        return values

    def descendants_of(self, roots: set[ConceptId | str]) -> frozenset[ConceptId]:
        frontier = {to_concept_id(root) for root in roots}
        descendants = set(frontier)
        changed = True
        while changed:
            changed = False
            for target, equation in self.equations.items():
                if target in descendants:
                    continue
                if any(parent in descendants for parent in equation.parents):
                    descendants.add(target)
                    changed = True
        return frozenset(descendants)

    def domain_for(self, concept_id: ConceptId | str) -> tuple[Value, ...]:
        name = to_concept_id(concept_id)
        if name in self.domains:
            return self.domains[name]
        actual = self.evaluate().get(name)
        if isinstance(actual, bool):
            return (False, True)
        return (actual,) if actual is not None else ()


def _structural_equation_from_edge(edge: ParameterizationEdge) -> StructuralEquation:
    def evaluate(values: Mapping[str, Value], *, edge: ParameterizationEdge = edge) -> Value:
        from propstore.propagation import (
            ParameterizationEvaluationStatus,
            evaluate_parameterization,
        )

        result = evaluate_parameterization(
            edge.sympy or "",
            {
                str(parent): float(values[str(parent)])
                for parent in edge.input_concept_ids
                if str(parent) in values
            },
            str(edge.output_concept_id),
        )
        if result.status is not ParameterizationEvaluationStatus.VALUE:
            raise ValueError(
                f"Could not evaluate structural equation for {edge.output_concept_id}"
            )
        return result.value

    return StructuralEquation(
        target=edge.output_concept_id,
        parents=edge.input_concept_ids,
        evaluate=evaluate,
        provenance=edge.provenance,
    )
