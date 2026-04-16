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
from typing import Any

from propstore.cel_checker import (
    ASTNode,
    BinaryOpNode,
    ConceptInfo,
    InNode,
    KindType,
    LiteralNode,
    NameNode,
    TernaryNode,
    UnaryOpNode,
    cel_registry_fingerprint,
    check_cel_condition_set,
    check_cel_expr,
)
from propstore.cel_types import (
    CelExpr,
    CheckedCelConditionSet,
    CheckedCelExpr,
    checked_condition_set,
)

import z3


class Z3TranslationError(Exception):
    """Raised when a CEL expression can't be translated to Z3."""


class Z3ConditionSolver:
    """Translates CEL conditions to Z3 and checks disjointness/equivalence."""

    def __init__(self, registry: dict[str, ConceptInfo]) -> None:
        self._registry = registry
        self._registry_fingerprint = cel_registry_fingerprint(registry)
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
        self._current_guards: list[Any] = []

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

    def _translate(self, node: ASTNode) -> Any:
        """Translate a CEL AST node to a Z3 expression."""
        if isinstance(node, LiteralNode):
            return self._translate_literal(node)
        if isinstance(node, NameNode):
            return self._translate_name(node)
        if isinstance(node, BinaryOpNode):
            return self._translate_binary(node)
        if isinstance(node, UnaryOpNode):
            return self._translate_unary(node)
        if isinstance(node, InNode):
            return self._translate_in(node)
        if isinstance(node, TernaryNode):
            return self._translate_ternary(node)
        raise Z3TranslationError(f"Unknown AST node type: {type(node)}")

    def _translate_literal(self, node: LiteralNode) -> Any:
        if node.lit_type in ("int", "float"):
            return z3.RealVal(node.value, self._ctx)
        if node.lit_type == "bool":
            return z3.BoolVal(node.value, self._ctx)
        if node.lit_type == "string":
            # String literals are resolved against enum sorts at comparison time
            # Return a sentinel — actual resolution happens in _translate_binary
            raise Z3TranslationError(
                f"Bare string literal '{node.value}' — should be resolved at comparison site"
            )
        raise Z3TranslationError(f"Unknown literal type: {node.lit_type}")

    def _translate_name(self, node: NameNode) -> Any:
        info = self._require_concept(node.name)
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            return self._get_real(node.name)
        if info.kind == KindType.BOOLEAN:
            return self._get_bool(node.name)
        if info.kind == KindType.CATEGORY:
            if info.category_extensible:
                return self._get_string(node.name)
            const, _ = self._get_enum(node.name)
            return const
        raise Z3TranslationError(
            f"Structural concept '{node.name}' cannot appear in CEL expressions"
        )

    def _translate_binary(self, node: BinaryOpNode) -> Any:
        # Logical operators
        if node.op == "&&":
            return z3.And(self._translate(node.left), self._translate(node.right))
        if node.op == "||":
            return z3.Or(self._translate(node.left), self._translate(node.right))

        # Category comparisons need special handling
        if node.op in ("==", "!="):
            result = self._try_category_comparison(node)
            if result is not None:
                return result

        left = self._translate(node.left)
        right = self._translate(node.right)

        # Arithmetic
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            # Guard against division by zero: Z3 treats x/0 as an
            # uninterpreted value (total function), which causes unsound
            # disjointness results. Collect non-zero guards to conjunct
            # into the final condition expression.
            zero = z3.RealVal(0, self._ctx)
            guard = right != zero
            self._current_guards.append(guard)
            return left / right

        # Comparisons
        if node.op == "<":
            return left < right
        if node.op == ">":
            return left > right
        if node.op == "<=":
            return left <= right
        if node.op == ">=":
            return left >= right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right

        raise Z3TranslationError(f"Unknown binary operator: {node.op}")

    def _try_category_comparison(self, node: BinaryOpNode) -> Any:
        """Handle category == 'value' or category != 'value'."""
        # Identify which side is the name and which is the string literal
        name_node, lit_node = None, None
        if isinstance(node.left, NameNode) and isinstance(node.right, LiteralNode) and node.right.lit_type == "string":
            name_node, lit_node = node.left, node.right
        elif isinstance(node.right, NameNode) and isinstance(node.left, LiteralNode) and node.left.lit_type == "string":
            name_node, lit_node = node.right, node.left
        else:
            return None

        info = self._require_concept(name_node.name)
        if info.kind != KindType.CATEGORY:
            return None

        if info.category_extensible:
            const = self._get_string(name_node.name)
            value = z3.StringVal(lit_node.value, self._ctx)
            if node.op == "==":
                return const == value
            if node.op == "!=":
                return const != value
            return None

        const, val_map = self._get_enum(name_node.name)
        z3_val = val_map.get(lit_node.value)
        if z3_val is None:
            raise Z3TranslationError(
                f"Unknown category value '{lit_node.value}' for concept '{name_node.name}'"
            )

        if node.op == "==":
            return const == z3_val
        if node.op == "!=":
            return const != z3_val
        return None

    def _translate_unary(self, node: UnaryOpNode) -> Any:
        if node.op == "!":
            return z3.Not(self._translate(node.operand))
        if node.op == "-":
            return -self._translate(node.operand)
        raise Z3TranslationError(f"Unknown unary operator: {node.op}")

    def _translate_in(self, node: InNode) -> Any:
        """Translate 'expr in [v1, v2, ...]'."""
        # Check if LHS is a category concept
        if isinstance(node.expr, NameNode):
            info = self._require_concept(node.expr.name)
            if info.kind == KindType.CATEGORY:
                if info.category_extensible:
                    const = self._get_string(node.expr.name)
                    clauses = []
                    for v in node.values:
                        if not isinstance(v, LiteralNode) or v.lit_type != "string":
                            raise Z3TranslationError("Non-string in category 'in' list")
                        clauses.append(const == z3.StringVal(v.value, self._ctx))
                    if not clauses:
                        return z3.BoolVal(False, self._ctx)
                    return z3.Or(*clauses) if len(clauses) > 1 else clauses[0]

                const, val_map = self._get_enum(node.expr.name)
                clauses = []
                for v in node.values:
                    if isinstance(v, LiteralNode) and v.lit_type == "string":
                        z3_val = val_map.get(v.value)
                        if z3_val is None:
                            raise Z3TranslationError(
                                f"Unknown category value '{v.value}' for concept '{node.expr.name}'"
                            )
                        clauses.append(const == z3_val)
                    else:
                        raise Z3TranslationError("Non-string in category 'in' list")
                if not clauses:
                    return z3.BoolVal(False, self._ctx)
                return z3.Or(*clauses) if len(clauses) > 1 else clauses[0]

        # Numeric 'in' — x in [1, 2, 3] -> x == 1 || x == 2 || x == 3
        lhs = self._translate(node.expr)
        clauses = []
        for v in node.values:
            clauses.append(lhs == self._translate(v))
        if not clauses:
            return z3.BoolVal(False, self._ctx)
        return z3.Or(*clauses) if len(clauses) > 1 else clauses[0]

    def _translate_ternary(self, node: TernaryNode) -> Any:
        cond = self._translate(node.condition)
        true_br = self._translate(node.true_branch)
        false_br = self._translate(node.false_branch)
        return z3.If(cond, true_br, false_br)

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
            self._current_guards: list[Any] = []
            translated = self._translate(checked.ast)
            # Conjunct any non-zero denominator guards collected during translation
            if self._current_guards:
                expr = z3.And(translated, *self._current_guards)
            else:
                expr = translated
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
        expr = self._condition_to_z3(condition)
        solver = z3.Solver(ctx=self._ctx)
        solver.add(expr)
        self._add_temporal_constraints(solver)
        for name, value in bindings.items():
            solver.add(self._binding_to_z3(name, value))
        return solver.check() == z3.sat

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
        expr_a = self._conditions_to_z3(conditions_a)
        expr_b = self._conditions_to_z3(conditions_b)
        solver = z3.Solver(ctx=self._ctx)
        solver.add(expr_a)
        solver.add(expr_b)
        self._add_temporal_constraints(solver)
        return solver.check() == z3.unsat

    def are_equivalent(
        self,
        conditions_a: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
        conditions_b: Sequence[CelExpr | CheckedCelExpr] | CheckedCelConditionSet,
    ) -> bool:
        """Check if two condition sets are logically equivalent.

        Both A∧¬B and B∧¬A must be UNSAT.
        """
        expr_a = self._conditions_to_z3(conditions_a)
        expr_b = self._conditions_to_z3(conditions_b)
        # Check A ∧ ¬B is UNSAT
        s1 = z3.Solver(ctx=self._ctx)
        s1.add(expr_a)
        s1.add(z3.Not(expr_b))
        self._add_temporal_constraints(s1)
        if s1.check() != z3.unsat:
            return False

        # Check B ∧ ¬A is UNSAT
        s2 = z3.Solver(ctx=self._ctx)
        s2.add(expr_b)
        s2.add(z3.Not(expr_a))
        self._add_temporal_constraints(s2)
        return s2.check() == z3.unsat

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
