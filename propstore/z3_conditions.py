"""Translate CEL condition ASTs into Z3 expressions for satisfiability queries.

Answers two questions about pairs of condition sets:
1. Are they disjoint? (conjunction is UNSAT)
2. Are they equivalent? (both A∧¬B and B∧¬A are UNSAT)

Uses z3.Real for quantity concepts, z3.Bool for boolean concepts, closed
enum semantics for non-extensible categories, and symbolic string semantics
for extensible categories. The CEL registry (dict[str, ConceptInfo])
determines which type each concept gets.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from cel_parser import (
    OP_ADD,
    OP_AND,
    OP_DIV,
    OP_EQ,
    OP_GE,
    OP_GT,
    OP_IN,
    OP_LE,
    OP_LT,
    OP_MUL,
    OP_NE,
    OP_NEG,
    OP_NOT,
    OP_OR,
    OP_SUB,
    OP_TERNARY,
    BoolLit,
    Call,
    CreateList,
    DoubleLit,
    Expr,
    Ident,
    IntLit,
    StringLit,
    UintLit,
)
from propstore.cel_checker import (
    check_cel_condition_set,
    check_cel_expr,
)
from propstore.cel_types import (
    CelExpr,
    CheckedCelConditionSet,
    CheckedCelExpr,
    checked_condition_set,
)
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    condition_registry_fingerprint,
)

import z3


_BINARY_OPS = frozenset(
    {
        OP_ADD, OP_SUB, OP_MUL, OP_DIV,
        OP_EQ, OP_NE, OP_LT, OP_LE, OP_GT, OP_GE,
        OP_AND, OP_OR,
    }
)


DEFAULT_Z3_TIMEOUT_MS = 30_000
"""Default Z3 budget for CEL queries.

Thirty seconds is long enough for the small CEL expressions propstore emits
while ensuring solver incompleteness reaches the caller as typed ignorance
instead of an unbounded hang.
"""


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


@dataclass(frozen=True)
class _Z3Projection:
    value: Any
    defined: Any


class Z3TranslationError(Exception):
    """Raised when a CEL expression can't be translated to Z3."""


class Z3UnknownError(Exception):
    """Raised when a legacy two-valued caller receives a Z3 unknown result."""

    def __init__(self, result: SolverUnknown) -> None:
        self.result = result
        super().__init__(f"Z3 returned UNKNOWN ({result.reason.value}): {result.hint}")


def _unknown_reason(hint: str) -> SolverUnknownReason:
    normalized = hint.lower()
    if "timeout" in normalized or "canceled" in normalized:
        return SolverUnknownReason.TIMEOUT
    if "incomplete" in normalized or "unknown" in normalized:
        return SolverUnknownReason.INCOMPLETE
    return SolverUnknownReason.OTHER


def solver_result_from_z3(solver: z3.Solver) -> SolverResult:
    check_result = solver.check()
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


class Z3ConditionSolver:
    """Translates CEL conditions to Z3 and checks disjointness/equivalence."""

    def __init__(
        self,
        registry: dict[str, ConceptInfo],
        *,
        timeout_ms: int = DEFAULT_Z3_TIMEOUT_MS,
    ) -> None:
        self._registry = MappingProxyType(
            {
                name: replace(info, category_values=list(info.category_values))
                for name, info in registry.items()
            }
        )
        self._registry_fingerprint = condition_registry_fingerprint(registry)
        if timeout_ms <= 0:
            raise ValueError("Z3 timeout must be a positive number of milliseconds")
        self._timeout_ms = timeout_ms
        self._ctx = z3.Context()
        self._reals: dict[str, z3.ArithRef] = {}
        self._bools: dict[str, z3.BoolRef] = {}
        self._strings: dict[str, z3.SeqRef] = {}
        self._checked_cache: dict[str, CheckedCelExpr] = {}
        self._condition_expr_cache: dict[tuple[str, str], Any] = {}
        self._condition_set_cache: dict[tuple[str, tuple[str, ...]], Any] = {}
        # For categories: one EnumSort per concept, with a z3 const
        self._enum_sorts: dict[str, z3.DatatypeSortRef] = {}
        self._enum_consts: dict[str, z3.ExprRef] = {}
        self._enum_values: dict[str, dict[str, z3.ExprRef]] = {}
        self._defined_true = z3.BoolVal(True, self._ctx)

    def _new_solver(self) -> z3.Solver:
        solver = z3.Solver(ctx=self._ctx)
        solver.set(timeout=self._timeout_ms)
        return solver

    def _get_real(self, name: str) -> z3.ArithRef:
        if name not in self._reals:
            self._reals[name] = z3.Real(name, self._ctx)
        return self._reals[name]

    def _get_bool(self, name: str) -> z3.BoolRef:
        if name not in self._bools:
            self._bools[name] = z3.Bool(name, self._ctx)
        return self._bools[name]

    def _get_string(self, name: str) -> z3.SeqRef:
        if name not in self._strings:
            self._strings[name] = z3.String(name, self._ctx)
        return self._strings[name]

    def _get_enum(self, name: str) -> tuple[z3.ExprRef, dict[str, z3.ExprRef]]:
        """Get or create an EnumSort for a closed category concept."""
        if name not in self._enum_consts:
            info = self._registry.get(name)
            values = list(info.category_values) if info else []
            if not values:
                raise Z3TranslationError(
                    f"Closed category concept '{name}' has no declared values"
                )
            sort, enum_vals = z3.EnumSort(f"{name}_Sort", values, self._ctx)
            self._enum_sorts[name] = sort
            const = z3.Const(name, sort)
            self._enum_consts[name] = const
            val_map = dict(zip(values, enum_vals))
            self._enum_values[name] = val_map
        return self._enum_consts[name], self._enum_values[name]

    def _require_concept(self, name: str) -> ConceptInfo:
        info = self._registry.get(name)
        if info is None:
            raise Z3TranslationError(f"Undefined concept: '{name}'")
        return info

    def _translate(self, node: Expr) -> _Z3Projection:
        """Translate a CEL AST node to a Z3 expression."""
        if isinstance(node, (IntLit, UintLit, DoubleLit)):
            return _Z3Projection(
                z3.RealVal(node.value, self._ctx), self._defined_true
            )
        if isinstance(node, BoolLit):
            return _Z3Projection(
                z3.BoolVal(node.value, self._ctx), self._defined_true
            )
        if isinstance(node, StringLit):
            raise Z3TranslationError(
                f"Bare string literal '{node.value}' — should be resolved at comparison site"
            )
        if isinstance(node, Ident):
            return self._translate_name(node)
        if isinstance(node, Call) and node.target is None:
            if node.function in _BINARY_OPS and len(node.args) == 2:
                return self._translate_binary(node)
            if node.function in (OP_NOT, OP_NEG) and len(node.args) == 1:
                return self._translate_unary(node)
            if node.function == OP_IN and len(node.args) == 2:
                return self._translate_in(node)
            if node.function == OP_TERNARY and len(node.args) == 3:
                return self._translate_ternary(node)
        raise Z3TranslationError(f"Unknown AST node type: {type(node).__name__}")

    def _translate_name(self, node: Ident) -> _Z3Projection:
        info = self._require_concept(node.name)
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            return _Z3Projection(self._get_real(node.name), self._defined_true)
        if info.kind == KindType.BOOLEAN:
            return _Z3Projection(self._get_bool(node.name), self._defined_true)
        if info.kind == KindType.CATEGORY:
            if info.category_extensible:
                return _Z3Projection(self._get_string(node.name), self._defined_true)
            const, _ = self._get_enum(node.name)
            return _Z3Projection(const, self._defined_true)
        raise Z3TranslationError(
            f"Structural concept '{node.name}' cannot appear in CEL expressions"
        )

    def _translate_binary(self, node: Call) -> _Z3Projection:
        op = node.function
        left_node, right_node = node.args
        if op == OP_AND:
            left = self._translate(left_node)
            right = self._translate(right_node)
            return _Z3Projection(
                z3.And(left.value, right.value),
                z3.Or(
                    z3.And(left.defined, z3.Not(left.value)),
                    z3.And(right.defined, z3.Not(right.value)),
                    z3.And(left.defined, right.defined),
                ),
            )
        if op == OP_OR:
            left = self._translate(left_node)
            right = self._translate(right_node)
            return _Z3Projection(
                z3.Or(left.value, right.value),
                z3.Or(
                    z3.And(left.defined, left.value),
                    z3.And(right.defined, right.value),
                    z3.And(left.defined, right.defined),
                ),
            )

        if op in (OP_EQ, OP_NE):
            result = self._try_category_comparison(node)
            if result is not None:
                return result

        left = self._translate(left_node)
        right = self._translate(right_node)
        defined = z3.And(left.defined, right.defined)

        if op == OP_ADD:
            return _Z3Projection(left.value + right.value, defined)
        if op == OP_SUB:
            return _Z3Projection(left.value - right.value, defined)
        if op == OP_MUL:
            return _Z3Projection(left.value * right.value, defined)
        if op == OP_DIV:
            zero = z3.RealVal(0, self._ctx)
            return _Z3Projection(
                left.value / right.value,
                z3.And(defined, right.value != zero),
            )

        if op == OP_LT:
            return _Z3Projection(left.value < right.value, defined)
        if op == OP_GT:
            return _Z3Projection(left.value > right.value, defined)
        if op == OP_LE:
            return _Z3Projection(left.value <= right.value, defined)
        if op == OP_GE:
            return _Z3Projection(left.value >= right.value, defined)
        if op == OP_EQ:
            return _Z3Projection(left.value == right.value, defined)
        if op == OP_NE:
            return _Z3Projection(left.value != right.value, defined)

        raise Z3TranslationError(f"Unknown binary operator: {op}")

    def _try_category_comparison(self, node: Call) -> _Z3Projection | None:
        """Handle category == 'value' or category != 'value'."""
        left_node, right_node = node.args
        name_node, lit_node = None, None
        if isinstance(left_node, Ident) and isinstance(right_node, StringLit):
            name_node, lit_node = left_node, right_node
        elif isinstance(right_node, Ident) and isinstance(left_node, StringLit):
            name_node, lit_node = right_node, left_node
        else:
            return None

        info = self._require_concept(name_node.name)
        if info.kind != KindType.CATEGORY:
            return None

        if info.category_extensible:
            const = self._get_string(name_node.name)
            value = z3.StringVal(lit_node.value, self._ctx)
            if node.function == OP_EQ:
                return _Z3Projection(const == value, self._defined_true)
            if node.function == OP_NE:
                return _Z3Projection(const != value, self._defined_true)
            return None

        const, val_map = self._get_enum(name_node.name)
        z3_val = val_map.get(lit_node.value)
        if z3_val is None:
            raise Z3TranslationError(
                f"Unknown category value '{lit_node.value}' for concept '{name_node.name}'"
            )

        if node.function == OP_EQ:
            return _Z3Projection(const == z3_val, self._defined_true)
        if node.function == OP_NE:
            return _Z3Projection(const != z3_val, self._defined_true)
        return None

    def _translate_unary(self, node: Call) -> _Z3Projection:
        operand = self._translate(node.args[0])
        if node.function == OP_NOT:
            return _Z3Projection(z3.Not(operand.value), operand.defined)
        if node.function == OP_NEG:
            return _Z3Projection(-operand.value, operand.defined)
        raise Z3TranslationError(f"Unknown unary operator: {node.function}")

    def _translate_in(self, node: Call) -> _Z3Projection:
        """Translate 'expr in [v1, v2, ...]'."""
        element, list_expr = node.args
        if not isinstance(list_expr, CreateList):
            raise Z3TranslationError("'in' rhs must be a list literal")
        values = list_expr.elements
        if isinstance(element, Ident):
            info = self._require_concept(element.name)
            if info.kind == KindType.CATEGORY:
                if info.category_extensible:
                    const = self._get_string(element.name)
                    clauses = []
                    for v in values:
                        if not isinstance(v, StringLit):
                            raise Z3TranslationError("Non-string in category 'in' list")
                        clauses.append(const == z3.StringVal(v.value, self._ctx))
                    if not clauses:
                        return _Z3Projection(z3.BoolVal(False, self._ctx), self._defined_true)
                    value = z3.Or(*clauses) if len(clauses) > 1 else clauses[0]
                    return _Z3Projection(value, self._defined_true)

                const, val_map = self._get_enum(element.name)
                clauses = []
                for v in values:
                    if isinstance(v, StringLit):
                        z3_val = val_map.get(v.value)
                        if z3_val is None:
                            raise Z3TranslationError(
                                f"Unknown category value '{v.value}' for concept '{element.name}'"
                            )
                        clauses.append(const == z3_val)
                    else:
                        raise Z3TranslationError("Non-string in category 'in' list")
                if not clauses:
                    return _Z3Projection(z3.BoolVal(False, self._ctx), self._defined_true)
                value = z3.Or(*clauses) if len(clauses) > 1 else clauses[0]
                return _Z3Projection(value, self._defined_true)

        lhs = self._translate(element)
        clauses = []
        defined = lhs.defined
        for v in values:
            projected = self._translate(v)
            defined = z3.And(defined, projected.defined)
            clauses.append(lhs.value == projected.value)
        if not clauses:
            return _Z3Projection(z3.BoolVal(False, self._ctx), defined)
        value = z3.Or(*clauses) if len(clauses) > 1 else clauses[0]
        return _Z3Projection(value, defined)

    def _translate_ternary(self, node: Call) -> _Z3Projection:
        cond_node, true_node, false_node = node.args
        cond = self._translate(cond_node)
        true_br = self._translate(true_node)
        false_br = self._translate(false_node)
        return _Z3Projection(
            z3.If(cond.value, true_br.value, false_br.value),
            z3.And(
                cond.defined,
                z3.Or(
                    z3.And(cond.value, true_br.defined),
                    z3.And(z3.Not(cond.value), false_br.defined),
                ),
            ),
        )

    def _ensure_checked_condition(self, condition: CelExpr | CheckedCelExpr) -> CheckedCelExpr:
        if isinstance(condition, CheckedCelExpr):
            self._require_matching_fingerprint(condition.registry_fingerprint)
            return condition
        source = str(condition)
        checked = self._checked_cache.get(source)
        if checked is None:
            try:
                checked = check_cel_expr(CelExpr(source), self._registry)
            except ValueError as exc:
                raise Z3TranslationError(str(exc)) from exc
            self._checked_cache[source] = checked
        return checked

    def _ensure_condition_set(
        self,
        conditions: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> CheckedCelConditionSet:
        if isinstance(conditions, CheckedCelConditionSet):
            self._require_matching_fingerprint(conditions.registry_fingerprint)
            return conditions
        checked_conditions = tuple(
            self._ensure_checked_condition(condition)
            for condition in conditions
        )
        if not checked_conditions:
            return check_cel_condition_set((), self._registry)
        return checked_condition_set(checked_conditions)

    def _require_matching_fingerprint(self, fingerprint: str) -> None:
        if fingerprint != self._registry_fingerprint:
            raise Z3TranslationError(
                "Checked CEL expression was validated against a different CEL registry"
            )

    def _condition_to_z3(self, condition: CelExpr | CheckedCelExpr) -> Any:
        checked = self._ensure_checked_condition(condition)
        key = (str(checked.registry_fingerprint), str(checked.source))
        expr = self._condition_expr_cache.get(key)
        if expr is None:
            translated = self._translate(checked.ast)
            expr = z3.And(translated.defined, translated.value)
            self._condition_expr_cache[key] = expr
        return expr

    def _conditions_to_z3(
        self,
        conditions: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> Any:
        """Translate a CEL condition set, conjuncting checked expressions."""
        condition_set = self._ensure_condition_set(conditions)
        normalized = tuple(str(source) for source in condition_set.sources)
        key = (str(condition_set.registry_fingerprint), normalized)
        expr = self._condition_set_cache.get(key)
        if expr is not None:
            return expr
        if not normalized:
            expr = z3.BoolVal(True, self._ctx)
        else:
            z3_exprs = [
                self._condition_to_z3(condition)
                for condition in condition_set.conditions
            ]
            expr = z3_exprs[0] if len(z3_exprs) == 1 else z3.And(*z3_exprs)
        self._condition_set_cache[key] = expr
        return expr

    def _binding_to_z3(self, name: str, value: Any) -> Any:
        info = self._require_concept(name)
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            return self._get_real(name) == z3.RealVal(value, self._ctx)
        if info.kind == KindType.BOOLEAN:
            return self._get_bool(name) == z3.BoolVal(bool(value), self._ctx)
        if info.kind == KindType.CATEGORY:
            if info.category_extensible:
                return self._get_string(name) == z3.StringVal(str(value), self._ctx)
            const, val_map = self._get_enum(name)
            z3_val = val_map.get(value)
            if z3_val is None:
                raise Z3TranslationError(
                    f"Unknown category value '{value}' for concept '{name}'"
                )
            return const == z3_val
        raise Z3TranslationError(
            f"Structural concept '{name}' cannot appear in CEL expressions"
        )

    def _temporal_ordering_constraints(self) -> list[Any]:
        """Generate valid_from <= valid_until constraints for timepoint interval pairs.

        Scans the registry for TIMEPOINT concepts whose names end in ``_from``
        and ``_until`` with a matching prefix (e.g. ``valid_from`` / ``valid_until``).
        For each such pair, emits ``from_var <= until_var`` so that Z3 never
        considers inverted intervals as satisfiable.

        This implements the well-formedness invariant described in
        reports/cyc-research-5-temporal-events.md §6.2: timepoints that form
        an interval must be ordered.
        """
        constraints: list[Any] = []
        from_concepts: dict[str, str] = {}  # prefix -> canonical_name
        until_concepts: dict[str, str] = {}

        for name, info in self._registry.items():
            if info.kind != KindType.TIMEPOINT:
                continue
            if name.endswith("_from"):
                from_concepts[name[: -len("_from")]] = name
            elif name.endswith("_until"):
                until_concepts[name[: -len("_until")]] = name

        for prefix, from_name in from_concepts.items():
            until_name = until_concepts.get(prefix)
            if until_name is None:
                continue
            # Only generate constraint if both variables have been
            # materialized (i.e., appear in conditions being checked).
            # We eagerly create them here so the constraint is always active.
            from_var = self._get_real(from_name)
            until_var = self._get_real(until_name)
            constraints.append(from_var <= until_var)

        return constraints

    def _add_temporal_constraints(self, solver: z3.Solver) -> None:
        """Inject well-formedness ordering into a solver before checking.

        Adds ``from_var <= until_var`` for every matched TIMEPOINT interval
        pair discovered by ``_temporal_ordering_constraints()``.  Called by
        ``are_disjoint``, ``are_equivalent``, and ``is_condition_satisfied``
        so that inverted intervals (e.g. valid_from=300, valid_until=100)
        are always treated as UNSAT.

        See Allen 1983 for the interval semantics and McCarthy 1993 for
        temporal context specialization.
        """
        for constraint in self._temporal_ordering_constraints():
            solver.add(constraint)

    def is_condition_satisfied(
        self,
        condition: CelExpr | CheckedCelExpr,
        bindings: Mapping[str, Any],
    ) -> bool:
        """Check whether one CEL condition holds under a concrete assignment."""
        result = _require_decided(
            self.is_condition_satisfied_result(condition, bindings)
        )
        return isinstance(result, SolverSat)

    def is_condition_satisfied_result(
        self,
        condition: CelExpr | CheckedCelExpr,
        bindings: Mapping[str, Any],
    ) -> SolverResult:
        """Check whether one CEL condition holds under a concrete assignment."""
        expr = self._condition_to_z3(condition)
        solver = self._new_solver()
        solver.add(expr)
        self._add_temporal_constraints(solver)
        for name, value in bindings.items():
            solver.add(self._binding_to_z3(name, value))
        return solver_result_from_z3(solver)

    def are_disjoint(
        self,
        conditions_a: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
        conditions_b: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> bool:
        """Check if two condition sets are disjoint (their conjunction is UNSAT).

        When TIMEPOINT interval pairs (e.g. valid_from/valid_until) are in the
        registry, the solver automatically adds valid_from <= valid_until so
        that inverted intervals are treated as UNSAT.
        """
        result = _require_decided(
            self.are_disjoint_result(conditions_a, conditions_b)
        )
        return isinstance(result, SolverUnsat)

    def are_disjoint_result(
        self,
        conditions_a: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
        conditions_b: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> SolverResult:
        """Return SAT/UNSAT/UNKNOWN for conjunction of two condition sets."""
        expr_a = self._conditions_to_z3(conditions_a)
        expr_b = self._conditions_to_z3(conditions_b)
        solver = self._new_solver()
        solver.add(expr_a)
        solver.add(expr_b)
        self._add_temporal_constraints(solver)
        return solver_result_from_z3(solver)

    def are_equivalent(
        self,
        conditions_a: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
        conditions_b: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> bool:
        """Check if two condition sets are logically equivalent.

        Both A∧¬B and B∧¬A must be UNSAT.
        """
        result = _require_decided(
            self.are_equivalent_result(conditions_a, conditions_b)
        )
        return isinstance(result, SolverUnsat)

    def are_equivalent_result(
        self,
        conditions_a: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
        conditions_b: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> SolverResult:
        """Return UNSAT iff two condition sets are logically equivalent."""
        expr_a = self._conditions_to_z3(conditions_a)
        expr_b = self._conditions_to_z3(conditions_b)
        # Check A ∧ ¬B is UNSAT
        s1 = self._new_solver()
        s1.add(expr_a)
        s1.add(z3.Not(expr_b))
        self._add_temporal_constraints(s1)
        left_result = solver_result_from_z3(s1)
        if not isinstance(left_result, SolverUnsat):
            return left_result

        # Check B ∧ ¬A is UNSAT
        s2 = self._new_solver()
        s2.add(expr_b)
        s2.add(z3.Not(expr_a))
        self._add_temporal_constraints(s2)
        return solver_result_from_z3(s2)

    def implies(
        self,
        antecedent_conditions: (
            Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet
        ),
        consequent_conditions: (
            Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet
        ),
    ) -> bool:
        """Check whether one condition set logically entails another."""
        result = _require_decided(
            self.implies_result(antecedent_conditions, consequent_conditions)
        )
        return isinstance(result, SolverUnsat)

    def implies_result(
        self,
        antecedent_conditions: (
            Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet
        ),
        consequent_conditions: (
            Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet
        ),
    ) -> SolverResult:
        """Return UNSAT iff antecedent conditions entail consequent conditions."""
        antecedent_expr = self._conditions_to_z3(antecedent_conditions)
        consequent_expr = self._conditions_to_z3(consequent_conditions)
        solver = self._new_solver()
        solver.add(antecedent_expr)
        solver.add(z3.Not(consequent_expr))
        self._add_temporal_constraints(solver)
        return solver_result_from_z3(solver)

    def partition_equivalence_classes(
        self,
        condition_sets: Sequence[
            Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet
        ],
    ) -> list[list[int]]:
        """Partition condition sets into equivalence classes.

        Returns list of groups, where each group is a list of indices
        into the input. Two condition sets are in the same group iff
        they are logically equivalent.

        Complexity: O(n * k) where k is the number of distinct classes,
        compared to O(n²) for pairwise checking.
        """
        if not condition_sets:
            return []

        # Each class is represented by (representative_conditions, [indices])
        representatives: list[Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet] = [
            condition_sets[0]
        ]
        classes: list[list[int]] = [[0]]

        for i in range(1, len(condition_sets)):
            matched = False
            for j, rep in enumerate(representatives):
                if self.are_equivalent(condition_sets[i], rep):
                    classes[j].append(i)
                    matched = True
                    break
            if not matched:
                representatives.append(condition_sets[i])
                classes.append([i])

        return classes
