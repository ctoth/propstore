"""Translate CEL condition ASTs into Z3 expressions for satisfiability queries.

Answers two questions about pairs of condition sets:
1. Are they disjoint? (conjunction is UNSAT)
2. Are they equivalent? (both A∧¬B and B∧¬A are UNSAT)

Uses z3.Real for quantity concepts, z3.EnumSort for category concepts,
and z3.Bool for boolean concepts. The CEL registry (dict[str, ConceptInfo])
determines which type each concept gets.
"""

from __future__ import annotations

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
    parse_cel,
)

import z3


class Z3TranslationError(Exception):
    """Raised when a CEL expression can't be translated to Z3."""


class Z3ConditionSolver:
    """Translates CEL conditions to Z3 and checks disjointness/equivalence."""

    def __init__(self, registry: dict[str, ConceptInfo]) -> None:
        self._registry = registry
        self._ctx = z3.Context()
        self._reals: dict[str, z3.ArithRef] = {}
        self._bools: dict[str, z3.BoolRef] = {}
        # For categories: one EnumSort per concept, with a z3 const
        self._enum_sorts: dict[str, z3.DatatypeSortRef] = {}
        self._enum_consts: dict[str, z3.ExprRef] = {}
        self._enum_values: dict[str, dict[str, z3.ExprRef]] = {}

    def _get_real(self, name: str) -> z3.ArithRef:
        if name not in self._reals:
            self._reals[name] = z3.Real(name, self._ctx)
        return self._reals[name]

    def _get_bool(self, name: str) -> z3.BoolRef:
        if name not in self._bools:
            self._bools[name] = z3.Bool(name, self._ctx)
        return self._bools[name]

    def _get_enum(self, name: str) -> tuple[z3.ExprRef, dict[str, z3.ExprRef]]:
        """Get or create an EnumSort for a category concept."""
        if name not in self._enum_consts:
            info = self._registry.get(name)
            values = list(info.category_values) if info else []
            if not values:
                # No known values — use a fresh uninterpreted sort
                sort = z3.DeclareSort(f"{name}_Sort", self._ctx)
                const = z3.Const(name, sort)
                self._enum_consts[name] = const
                self._enum_values[name] = {}
                return const, {}
            sort, enum_vals = z3.EnumSort(f"{name}_Sort", values, self._ctx)
            self._enum_sorts[name] = sort
            const = z3.Const(name, sort)
            self._enum_consts[name] = const
            val_map = dict(zip(values, enum_vals))
            self._enum_values[name] = val_map
        return self._enum_consts[name], self._enum_values[name]

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
        info = self._registry.get(node.name)
        if info is None:
            # Unknown concept — treat as real (most permissive)
            return self._get_real(node.name)
        if info.kind == KindType.QUANTITY:
            return self._get_real(node.name)
        if info.kind == KindType.BOOLEAN:
            return self._get_bool(node.name)
        if info.kind == KindType.CATEGORY:
            const, _ = self._get_enum(node.name)
            return const
        # STRUCTURAL or unknown — treat as real
        return self._get_real(node.name)

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

        info = self._registry.get(name_node.name)
        if info is None or info.kind != KindType.CATEGORY:
            return None

        const, val_map = self._get_enum(name_node.name)
        z3_val = val_map.get(lit_node.value)
        if z3_val is None:
            # Value not in known set — can't translate
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
            info = self._registry.get(node.expr.name)
            if info and info.kind == KindType.CATEGORY:
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

    def _conditions_to_z3(self, conditions: list[str]) -> Any:
        """Parse and translate a list of CEL condition strings, conjuncting them."""
        if not conditions:
            return z3.BoolVal(True, self._ctx)
        z3_exprs = []
        for cond_str in conditions:
            ast = parse_cel(cond_str)
            z3_exprs.append(self._translate(ast))
        if len(z3_exprs) == 1:
            return z3_exprs[0]
        return z3.And(*z3_exprs)

    def are_disjoint(self, conditions_a: list[str], conditions_b: list[str]) -> bool:
        """Check if two condition sets are disjoint (their conjunction is UNSAT)."""
        try:
            expr_a = self._conditions_to_z3(conditions_a)
            expr_b = self._conditions_to_z3(conditions_b)
        except (Z3TranslationError, ValueError):
            return False  # Can't determine — assume not disjoint (conservative)

        solver = z3.Solver(ctx=self._ctx)
        solver.add(expr_a)
        solver.add(expr_b)
        return solver.check() == z3.unsat

    def are_equivalent(self, conditions_a: list[str], conditions_b: list[str]) -> bool:
        """Check if two condition sets are logically equivalent.

        Both A∧¬B and B∧¬A must be UNSAT.
        """
        try:
            expr_a = self._conditions_to_z3(conditions_a)
            expr_b = self._conditions_to_z3(conditions_b)
        except (Z3TranslationError, ValueError):
            return False  # Can't determine — assume not equivalent

        # Check A ∧ ¬B is UNSAT
        s1 = z3.Solver(ctx=self._ctx)
        s1.add(expr_a)
        s1.add(z3.Not(expr_b))
        if s1.check() != z3.unsat:
            return False

        # Check B ∧ ¬A is UNSAT
        s2 = z3.Solver(ctx=self._ctx)
        s2.add(expr_b)
        s2.add(z3.Not(expr_a))
        return s2.check() == z3.unsat

    def partition_equivalence_classes(
        self, condition_sets: list[list[str]]
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
        representatives: list[list[str]] = [condition_sets[0]]
        classes: list[list[int]] = [[0]]

        for i in range(1, len(condition_sets)):
            matched = False
            for j, rep in enumerate(representatives):
                try:
                    if self.are_equivalent(condition_sets[i], rep):
                        classes[j].append(i)
                        matched = True
                        break
                except Exception:
                    continue
            if not matched:
                representatives.append(condition_sets[i])
                classes.append([i])

        return classes
