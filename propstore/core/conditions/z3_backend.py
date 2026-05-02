"""Z3 backend for semantic ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import z3

from propstore.core.conditions.ir import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionIR,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionUnary,
    ConditionUnaryOp,
    ConditionValueKind,
)
from propstore.core.conditions.registry import ConceptInfo, KindType


@dataclass(frozen=True)
class Z3Projection:
    term: Any
    defined: Any


class ConditionZ3Encoder:
    """Project checked condition IR into a single Z3 context."""

    def __init__(
        self,
        registry: Mapping[str, ConceptInfo] | None = None,
        *,
        ctx: z3.Context | None = None,
    ) -> None:
        self._registry = registry or {}
        self.ctx = ctx or z3.Context()
        self.true = z3.BoolVal(True, self.ctx)
        self.false = z3.BoolVal(False, self.ctx)
        self._reals: dict[str, Any] = {}
        self._bools: dict[str, Any] = {}
        self._strings: dict[str, Any] = {}
        self._enum_consts: dict[str, Any] = {}
        self._enum_values: dict[str, dict[str, Any]] = {}

    def condition_to_z3(self, condition: ConditionIR) -> Any:
        projection = self.project(condition)
        if z3.is_bool(projection.term):
            return z3.And(projection.defined, projection.term)
        return projection.term

    def project(self, condition: ConditionIR) -> Z3Projection:
        if isinstance(condition, ConditionLiteral):
            return self._project_literal(condition)
        if isinstance(condition, ConditionReference):
            return Z3Projection(self._reference_term(condition), self.true)
        if isinstance(condition, ConditionUnary):
            operand = self.project(condition.operand)
            if condition.op == ConditionUnaryOp.NOT:
                return Z3Projection(z3.Not(operand.term), operand.defined)
            if condition.op == ConditionUnaryOp.NEGATE:
                return Z3Projection(-operand.term, operand.defined)
            raise ValueError(f"unsupported unary condition op: {condition.op}")
        if isinstance(condition, ConditionBinary):
            return self._project_binary(condition)
        if isinstance(condition, ConditionMembership):
            return self._project_membership(condition)
        if isinstance(condition, ConditionChoice):
            return self._project_choice(condition)
        raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")

    def binding_constraint(self, name: str, value: object) -> Any:
        info = self._require_registry_concept(name)
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError(f"expected numeric binding for {name}")
            return self._get_real(name) == z3.RealVal(value, self.ctx)
        if info.kind == KindType.BOOLEAN:
            if not isinstance(value, bool):
                raise TypeError(f"expected boolean binding for {name}")
            return self._get_bool(name) == z3.BoolVal(value, self.ctx)
        if info.kind == KindType.CATEGORY:
            if info.category_extensible:
                if not isinstance(value, str):
                    raise TypeError(f"expected string binding for {name}")
                return self._get_string(name) == z3.StringVal(value, self.ctx)
            const, val_map = self._get_enum(name, info.category_values)
            z3_value = val_map.get(str(value))
            if z3_value is None:
                raise Z3BackendTranslationError(
                    f"Unknown category value '{value}' for concept '{name}'"
                )
            return const == z3_value
        raise Z3BackendTranslationError(
            f"Structural concept '{name}' cannot appear in conditions"
        )

    def temporal_ordering_constraints(self) -> tuple[Any, ...]:
        from_concepts: dict[str, str] = {}
        until_concepts: dict[str, str] = {}
        for name, info in self._registry.items():
            if info.kind != KindType.TIMEPOINT:
                continue
            if name.endswith("_from"):
                from_concepts[name[: -len("_from")]] = name
            elif name.endswith("_until"):
                until_concepts[name[: -len("_until")]] = name
        return tuple(
            self._get_real(from_name) <= self._get_real(until_name)
            for prefix, from_name in sorted(from_concepts.items())
            for until_name in (until_concepts.get(prefix),)
            if until_name is not None
        )

    def reference_binding_constraints(
        self,
        condition: ConditionIR,
        bindings: Mapping[str, object],
    ) -> tuple[Any, ...]:
        references = _reference_kinds(condition)
        constraints: list[Any] = []
        for name in sorted(references):
            if name not in bindings:
                raise ValueError(f"missing binding: {name}")
            constraints.append(
                self._binding_constraint_for_kind(name, references[name], bindings[name])
            )
        return tuple(constraints)

    def _project_literal(self, condition: ConditionLiteral) -> Z3Projection:
        if condition.value_kind == ConditionValueKind.BOOLEAN:
            return Z3Projection(z3.BoolVal(condition.value, self.ctx), self.true)
        if condition.value_kind in (
            ConditionValueKind.NUMERIC,
            ConditionValueKind.TIMEPOINT,
        ):
            return Z3Projection(z3.RealVal(condition.value, self.ctx), self.true)
        if condition.value_kind == ConditionValueKind.STRING:
            return Z3Projection(z3.StringVal(condition.value, self.ctx), self.true)
        raise TypeError(f"unsupported ConditionIR literal for Z3: {condition.value!r}")

    def _reference_term(self, condition: ConditionReference) -> Any:
        if condition.value_kind == ConditionValueKind.BOOLEAN:
            return self._get_bool(condition.source_name)
        if condition.value_kind in (
            ConditionValueKind.NUMERIC,
            ConditionValueKind.TIMEPOINT,
        ):
            return self._get_real(condition.source_name)
        if condition.value_kind == ConditionValueKind.STRING:
            if condition.category_extensible is False:
                const, _ = self._get_enum(condition.source_name, condition.category_values)
                return const
            return self._get_string(condition.source_name)
        raise ValueError(
            f"unsupported ConditionIR reference kind for Z3: {condition.value_kind}"
        )

    def _project_binary(self, condition: ConditionBinary) -> Z3Projection:
        if condition.op == ConditionBinaryOp.AND:
            left = self.project(condition.left)
            right = self.project(condition.right)
            return Z3Projection(
                z3.And(left.term, right.term),
                z3.Or(
                    z3.And(left.defined, z3.Not(left.term)),
                    z3.And(right.defined, z3.Not(right.term)),
                    z3.And(left.defined, right.defined),
                ),
            )
        if condition.op == ConditionBinaryOp.OR:
            left = self.project(condition.left)
            right = self.project(condition.right)
            return Z3Projection(
                z3.Or(left.term, right.term),
                z3.Or(
                    z3.And(left.defined, left.term),
                    z3.And(right.defined, right.term),
                    z3.And(left.defined, right.defined),
                ),
            )
        if condition.op in (ConditionBinaryOp.EQUAL, ConditionBinaryOp.NOT_EQUAL):
            category = self._category_comparison(condition)
            if category is not None:
                return category

        left = self.project(condition.left)
        right = self.project(condition.right)
        defined = z3.And(left.defined, right.defined)

        if condition.op == ConditionBinaryOp.EQUAL:
            return Z3Projection(left.term == right.term, defined)
        if condition.op == ConditionBinaryOp.NOT_EQUAL:
            return Z3Projection(left.term != right.term, defined)
        if condition.op == ConditionBinaryOp.LESS_THAN:
            return Z3Projection(left.term < right.term, defined)
        if condition.op == ConditionBinaryOp.LESS_THAN_OR_EQUAL:
            return Z3Projection(left.term <= right.term, defined)
        if condition.op == ConditionBinaryOp.GREATER_THAN:
            return Z3Projection(left.term > right.term, defined)
        if condition.op == ConditionBinaryOp.GREATER_THAN_OR_EQUAL:
            return Z3Projection(left.term >= right.term, defined)
        if condition.op == ConditionBinaryOp.ADD:
            return Z3Projection(left.term + right.term, defined)
        if condition.op == ConditionBinaryOp.SUBTRACT:
            return Z3Projection(left.term - right.term, defined)
        if condition.op == ConditionBinaryOp.MULTIPLY:
            return Z3Projection(left.term * right.term, defined)
        if condition.op == ConditionBinaryOp.DIVIDE:
            return Z3Projection(
                left.term / right.term,
                z3.And(defined, right.term != z3.RealVal(0, self.ctx)),
            )
        raise ValueError(f"unsupported binary condition op: {condition.op}")

    def _category_comparison(
        self,
        condition: ConditionBinary,
    ) -> Z3Projection | None:
        pair = self._reference_string_literal_pair(condition.left, condition.right)
        if pair is None:
            pair = self._reference_string_literal_pair(condition.right, condition.left)
        if pair is None:
            return None

        reference, literal = pair
        if reference.category_extensible is None:
            return None
        ref_term = self._reference_term(reference)
        literal_term = self._category_literal_for_reference(reference, literal)
        if condition.op == ConditionBinaryOp.EQUAL:
            return Z3Projection(ref_term == literal_term, self.true)
        return Z3Projection(ref_term != literal_term, self.true)

    def _project_membership(self, condition: ConditionMembership) -> Z3Projection:
        if (
            isinstance(condition.element, ConditionReference)
            and condition.element.category_extensible is not None
        ):
            element = self.project(condition.element)
            clauses = tuple(
                element.term
                == self._category_literal_for_reference(condition.element, option)
                for option in condition.options
            )
            if not clauses:
                return Z3Projection(self.false, self.true)
            if len(clauses) == 1:
                return Z3Projection(clauses[0], self.true)
            return Z3Projection(z3.Or(*clauses), self.true)

        element = self.project(condition.element)
        options = tuple(self.project(option) for option in condition.options)
        defined = z3.And(element.defined, *(option.defined for option in options))
        clauses = tuple(element.term == option.term for option in options)
        if not clauses:
            return Z3Projection(self.false, defined)
        if len(clauses) == 1:
            return Z3Projection(clauses[0], defined)
        return Z3Projection(z3.Or(*clauses), defined)

    def _project_choice(self, condition: ConditionChoice) -> Z3Projection:
        test = self.project(condition.condition)
        when_true = self.project(condition.when_true)
        when_false = self.project(condition.when_false)
        return Z3Projection(
            z3.If(test.term, when_true.term, when_false.term),
            z3.And(
                test.defined,
                z3.Or(
                    z3.And(test.term, when_true.defined),
                    z3.And(z3.Not(test.term), when_false.defined),
                ),
            ),
        )

    def _category_literal_for_reference(
        self,
        reference: ConditionReference,
        literal: ConditionIR,
    ) -> Any:
        if not (
            isinstance(literal, ConditionLiteral)
            and literal.value_kind == ConditionValueKind.STRING
        ):
            raise Z3BackendTranslationError("Non-string in category 'in' list")
        literal_value = str(literal.value)
        if reference.category_extensible:
            return z3.StringVal(literal_value, self.ctx)
        _, val_map = self._get_enum(reference.source_name, reference.category_values)
        z3_value = val_map.get(literal_value)
        if z3_value is None:
            raise Z3BackendTranslationError(
                f"Unknown category value '{literal_value}' for concept "
                f"'{reference.source_name}'"
            )
        return z3_value

    def _reference_string_literal_pair(
        self,
        left: ConditionIR,
        right: ConditionIR,
    ) -> tuple[ConditionReference, ConditionLiteral] | None:
        if (
            isinstance(left, ConditionReference)
            and isinstance(right, ConditionLiteral)
            and right.value_kind == ConditionValueKind.STRING
        ):
            return left, right
        return None

    def _get_real(self, name: str) -> Any:
        if name not in self._reals:
            self._reals[name] = z3.Real(name, self.ctx)
        return self._reals[name]

    def _get_bool(self, name: str) -> Any:
        if name not in self._bools:
            self._bools[name] = z3.Bool(name, self.ctx)
        return self._bools[name]

    def _get_string(self, name: str) -> Any:
        if name not in self._strings:
            self._strings[name] = z3.String(name, self.ctx)
        return self._strings[name]

    def _get_enum(
        self,
        name: str,
        values: tuple[str, ...] | list[str],
    ) -> tuple[Any, dict[str, Any]]:
        if name not in self._enum_consts:
            if not values:
                raise Z3BackendTranslationError(
                    f"Closed category concept '{name}' has no declared values"
                )
            sort, enum_values = z3.EnumSort(f"{name}_Sort", list(values), self.ctx)
            self._enum_consts[name] = z3.Const(name, sort)
            self._enum_values[name] = dict(zip(values, enum_values, strict=True))
        return self._enum_consts[name], self._enum_values[name]

    def _require_registry_concept(self, name: str) -> ConceptInfo:
        info = self._registry.get(name)
        if info is None:
            raise Z3BackendTranslationError(f"Undefined concept: '{name}'")
        return info

    def _binding_constraint_for_kind(
        self,
        name: str,
        value_kind: ConditionValueKind,
        value: object,
    ) -> Any:
        if value_kind in (ConditionValueKind.NUMERIC, ConditionValueKind.TIMEPOINT):
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError(f"expected numeric binding for {name}")
            return self._get_real(name) == z3.RealVal(value, self.ctx)
        if value_kind == ConditionValueKind.BOOLEAN:
            if not isinstance(value, bool):
                raise TypeError(f"expected boolean binding for {name}")
            return self._get_bool(name) == z3.BoolVal(value, self.ctx)
        if value_kind == ConditionValueKind.STRING:
            if not isinstance(value, str):
                raise TypeError(f"expected string binding for {name}")
            return self._get_string(name) == z3.StringVal(value, self.ctx)
        raise ValueError(f"unsupported ConditionIR binding kind for {name}: {value_kind}")


class Z3BackendTranslationError(Exception):
    """Raised when ConditionIR cannot be represented in Z3."""


def condition_ir_to_z3(condition: ConditionIR) -> Any:
    return ConditionZ3Encoder().condition_to_z3(condition)


def z3_bindings_for_values(
    condition: ConditionIR,
    bindings: Mapping[str, object],
) -> tuple[Any, ...]:
    return ConditionZ3Encoder().reference_binding_constraints(condition, bindings)


def _reference_kinds(condition: ConditionIR) -> dict[str, ConditionValueKind]:
    references: dict[str, ConditionValueKind] = {}
    _collect_reference_kinds(condition, references)
    return references


def _collect_reference_kinds(
    condition: ConditionIR,
    references: dict[str, ConditionValueKind],
) -> None:
    if isinstance(condition, ConditionReference):
        existing = references.get(condition.source_name)
        if existing is not None and existing != condition.value_kind:
            raise ValueError(
                f"conflicting ConditionIR kinds for binding: {condition.source_name}"
            )
        references[condition.source_name] = condition.value_kind
        return
    if isinstance(condition, ConditionLiteral):
        return
    if isinstance(condition, ConditionUnary):
        _collect_reference_kinds(condition.operand, references)
        return
    if isinstance(condition, ConditionBinary):
        _collect_reference_kinds(condition.left, references)
        _collect_reference_kinds(condition.right, references)
        return
    if isinstance(condition, ConditionMembership):
        _collect_reference_kinds(condition.element, references)
        for option in condition.options:
            _collect_reference_kinds(option, references)
        return
    if isinstance(condition, ConditionChoice):
        _collect_reference_kinds(condition.condition, references)
        _collect_reference_kinds(condition.when_true, references)
        _collect_reference_kinds(condition.when_false, references)
        return
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")
