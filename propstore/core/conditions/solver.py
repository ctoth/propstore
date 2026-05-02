"""Public semantic condition solver over checked ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import z3

from propstore.core.conditions.checked import (
    CheckedCondition,
    CheckedConditionSet,
    checked_condition_set,
)
from propstore.core.conditions.registry import (
    ConceptInfo,
    condition_registry_fingerprint,
)
from propstore.core.conditions.z3_backend import (
    ConditionZ3Encoder,
    Z3BackendTranslationError,
)


DEFAULT_Z3_TIMEOUT_MS = 30_000
"""Default Z3 budget for condition queries."""


class SolverUnknownReason(StrEnum):
    TIMEOUT = "timeout"
    INCOMPLETE = "incomplete"
    OTHER = "other"


@dataclass(frozen=True)
class SolverSat:
    model: object | None = None


@dataclass(frozen=True)
class SolverUnsat:
    unsat_core: tuple[str, ...] = ()


@dataclass(frozen=True)
class SolverUnknown:
    reason: SolverUnknownReason
    hint: str


SolverResult = SolverSat | SolverUnsat | SolverUnknown


class Z3TranslationError(Exception):
    """Raised when checked ConditionIR cannot be translated to Z3."""


class Z3UnknownError(Exception):
    """Raised when a two-valued caller receives a Z3 unknown result."""

    def __init__(self, result: SolverUnknown) -> None:
        self.result = result
        super().__init__(f"Z3 returned UNKNOWN ({result.reason.value}): {result.hint}")


def solver_result_from_z3(solver: z3.Solver) -> SolverResult:
    try:
        check_result = solver.check()
    except z3.Z3Exception as exc:
        raise Z3TranslationError(str(exc)) from exc
    if check_result == z3.sat:
        return SolverSat(solver.model())
    if check_result == z3.unsat:
        return SolverUnsat(tuple(str(entry) for entry in solver.unsat_core()))
    hint = solver.reason_unknown() or "z3 returned unknown without a reason"
    return SolverUnknown(_unknown_reason(hint), hint)


def _require_decided(result: SolverResult) -> SolverSat | SolverUnsat:
    if isinstance(result, SolverUnknown):
        raise Z3UnknownError(result)
    return result


class ConditionSolver:
    """Answers semantic queries over checked condition carriers."""

    def __init__(
        self,
        registry: Mapping[str, ConceptInfo],
        *,
        timeout_ms: int = DEFAULT_Z3_TIMEOUT_MS,
    ) -> None:
        if timeout_ms <= 0:
            raise ValueError("Z3 timeout must be a positive number of milliseconds")
        self._registry = MappingProxyType(
            {
                name: replace(info, category_values=list(info.category_values))
                for name, info in registry.items()
            }
        )
        self._registry_fingerprint = condition_registry_fingerprint(self._registry)
        self._timeout_ms = timeout_ms
        self._ctx = z3.Context()
        self._encoder = ConditionZ3Encoder(self._registry, ctx=self._ctx)
        self._condition_expr_cache: dict[tuple[str, str], Any] = {}
        self._condition_set_cache: dict[tuple[str, tuple[str, ...]], Any] = {}

    @property
    def registry_fingerprint(self) -> str:
        return str(self._registry_fingerprint)

    @property
    def registry(self) -> Mapping[str, ConceptInfo]:
        return self._registry

    def is_condition_satisfied(
        self,
        condition: CheckedCondition,
        bindings: Mapping[str, Any],
    ) -> bool:
        result = _require_decided(
            self.is_condition_satisfied_result(condition, bindings)
        )
        return isinstance(result, SolverSat)

    def is_condition_satisfied_result(
        self,
        condition: CheckedCondition,
        bindings: Mapping[str, Any],
    ) -> SolverResult:
        try:
            expr = self._condition_to_z3(condition)
            solver = self._new_solver()
            solver.add(expr)
            self._add_temporal_constraints(solver)
            for name, value in bindings.items():
                solver.add(self._binding_to_z3(name, value))
            return solver_result_from_z3(solver)
        except z3.Z3Exception as exc:
            raise Z3TranslationError(str(exc)) from exc

    def are_disjoint(
        self,
        conditions_a: Sequence[CheckedCondition] | CheckedConditionSet,
        conditions_b: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> bool:
        result = _require_decided(
            self.are_disjoint_result(conditions_a, conditions_b)
        )
        return isinstance(result, SolverUnsat)

    def are_disjoint_result(
        self,
        conditions_a: Sequence[CheckedCondition] | CheckedConditionSet,
        conditions_b: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> SolverResult:
        try:
            expr_a = self._conditions_to_z3(conditions_a)
            expr_b = self._conditions_to_z3(conditions_b)
            solver = self._new_solver()
            solver.add(expr_a)
            solver.add(expr_b)
            self._add_temporal_constraints(solver)
            return solver_result_from_z3(solver)
        except z3.Z3Exception as exc:
            raise Z3TranslationError(str(exc)) from exc

    def are_equivalent(
        self,
        conditions_a: Sequence[CheckedCondition] | CheckedConditionSet,
        conditions_b: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> bool:
        result = _require_decided(
            self.are_equivalent_result(conditions_a, conditions_b)
        )
        return isinstance(result, SolverUnsat)

    def are_equivalent_result(
        self,
        conditions_a: Sequence[CheckedCondition] | CheckedConditionSet,
        conditions_b: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> SolverResult:
        try:
            expr_a = self._conditions_to_z3(conditions_a)
            expr_b = self._conditions_to_z3(conditions_b)
            first = self._new_solver()
            first.add(expr_a)
            first.add(z3.Not(expr_b))
            self._add_temporal_constraints(first)
            left_result = solver_result_from_z3(first)
            if not isinstance(left_result, SolverUnsat):
                return left_result

            second = self._new_solver()
            second.add(expr_b)
            second.add(z3.Not(expr_a))
            self._add_temporal_constraints(second)
            return solver_result_from_z3(second)
        except z3.Z3Exception as exc:
            raise Z3TranslationError(str(exc)) from exc

    def implies(
        self,
        antecedent_conditions: Sequence[CheckedCondition] | CheckedConditionSet,
        consequent_conditions: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> bool:
        result = _require_decided(
            self.implies_result(antecedent_conditions, consequent_conditions)
        )
        return isinstance(result, SolverUnsat)

    def implies_result(
        self,
        antecedent_conditions: Sequence[CheckedCondition] | CheckedConditionSet,
        consequent_conditions: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> SolverResult:
        try:
            antecedent_expr = self._conditions_to_z3(antecedent_conditions)
            consequent_expr = self._conditions_to_z3(consequent_conditions)
            solver = self._new_solver()
            solver.add(antecedent_expr)
            solver.add(z3.Not(consequent_expr))
            self._add_temporal_constraints(solver)
            return solver_result_from_z3(solver)
        except z3.Z3Exception as exc:
            raise Z3TranslationError(str(exc)) from exc

    def partition_equivalence_classes(
        self,
        condition_sets: Sequence[Sequence[CheckedCondition] | CheckedConditionSet],
    ) -> list[list[int]]:
        if not condition_sets:
            return []

        representatives: list[Sequence[CheckedCondition] | CheckedConditionSet] = [
            condition_sets[0]
        ]
        classes: list[list[int]] = [[0]]

        for index in range(1, len(condition_sets)):
            matched = False
            for rep_index, representative in enumerate(representatives):
                if self.are_equivalent(condition_sets[index], representative):
                    classes[rep_index].append(index)
                    matched = True
                    break
            if not matched:
                representatives.append(condition_sets[index])
                classes.append([index])
        return classes

    def _new_solver(self) -> z3.Solver:
        solver = z3.Solver(ctx=self._ctx)
        solver.set(timeout=self._timeout_ms)
        return solver

    def _condition_to_z3(self, condition: CheckedCondition) -> Any:
        self._require_matching_fingerprint(condition.registry_fingerprint)
        key = (str(condition.registry_fingerprint), condition.source)
        expr = self._condition_expr_cache.get(key)
        if expr is not None:
            return expr
        try:
            expr = self._encoder.condition_to_z3(condition.ir)
        except Z3BackendTranslationError as exc:
            raise Z3TranslationError(str(exc)) from exc
        self._condition_expr_cache[key] = expr
        return expr

    def _conditions_to_z3(
        self,
        conditions: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> Any:
        condition_set = self._ensure_condition_set(conditions)
        normalized = tuple(condition.source for condition in condition_set.conditions)
        key = (str(condition_set.registry_fingerprint), normalized)
        expr = self._condition_set_cache.get(key)
        if expr is not None:
            return expr
        if not normalized:
            expr = z3.BoolVal(True, self._ctx)
        else:
            terms = [
                self._condition_to_z3(condition)
                for condition in condition_set.conditions
            ]
            expr = terms[0] if len(terms) == 1 else z3.And(*terms)
        self._condition_set_cache[key] = expr
        return expr

    def _ensure_condition_set(
        self,
        conditions: Sequence[CheckedCondition] | CheckedConditionSet,
    ) -> CheckedConditionSet:
        if isinstance(conditions, CheckedConditionSet):
            if conditions.conditions:
                self._require_matching_fingerprint(conditions.registry_fingerprint)
            return conditions
        condition_set = checked_condition_set(conditions)
        if condition_set.conditions:
            self._require_matching_fingerprint(condition_set.registry_fingerprint)
        return condition_set

    def _require_matching_fingerprint(self, fingerprint: str) -> None:
        if fingerprint != self._registry_fingerprint:
            raise Z3TranslationError(
                "Checked condition was validated against a different condition registry"
            )

    def _binding_to_z3(self, name: str, value: object) -> Any:
        try:
            return self._encoder.binding_constraint(name, value)
        except Z3BackendTranslationError as exc:
            raise Z3TranslationError(str(exc)) from exc

    def _add_temporal_constraints(self, solver: z3.Solver) -> None:
        for constraint in self._encoder.temporal_ordering_constraints():
            solver.add(constraint)


def _unknown_reason(hint: str) -> SolverUnknownReason:
    normalized = hint.lower()
    if "timeout" in normalized or "canceled" in normalized:
        return SolverUnknownReason.TIMEOUT
    if "incomplete" in normalized or "unknown" in normalized:
        return SolverUnknownReason.INCOMPLETE
    return SolverUnknownReason.OTHER
