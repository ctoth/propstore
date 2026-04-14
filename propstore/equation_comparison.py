"""Typed equation normalization and structural comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING

from propstore.equation_parser import (
    BinaryExpr,
    EquationFailure,
    EquationFailureCode,
    EquationSymbolBinding,
    EquationExpr,
    FunctionExpr,
    NumberExpr,
    ParsedEquation,
    SymbolExpr,
    UnaryExpr,
    parse_equation,
    structural_signature as ast_structural_signature,
)

if TYPE_CHECKING:
    from propstore.conflict_detector.models import ConflictClaim


@dataclass(frozen=True)
class EquationNormalization:
    canonical: str
    source_text: str
    structural_signature: str


class EquationComparisonStatus(StrEnum):
    EQUIVALENT = "equivalent"
    DIFFERENT = "different"
    INCOMPARABLE = "incomparable"


@dataclass(frozen=True)
class EquationComparison:
    status: EquationComparisonStatus
    left: EquationNormalization | EquationFailure
    right: EquationNormalization | EquationFailure


_sympy = None


def equation_signature(claim: ConflictClaim) -> tuple[str, tuple[str, ...]] | None:
    """Build a concept-based grouping signature for typed equation claims."""
    variables = claim.variables
    if not variables:
        return None

    dependent_concepts = [
        variable.concept_id
        for variable in variables
        if variable.role == "dependent" and variable.concept_id
    ]
    if len(dependent_concepts) != 1:
        return None

    dependent_concept = dependent_concepts[0]
    independent_concepts = sorted(
        variable.concept_id
        for variable in variables
        if variable.concept_id and variable.concept_id != dependent_concept
    )
    return dependent_concept, tuple(independent_concepts)


def canonicalize_equation(claim: ConflictClaim) -> EquationNormalization | EquationFailure:
    """Normalize a typed equation claim onto a deterministic canonical form."""
    bindings = _claim_bindings(claim)
    if isinstance(bindings, EquationFailure):
        return bindings

    source_text = _claim_source_text(claim)
    if source_text is None:
        return EquationFailure(
            code=EquationFailureCode.MISSING_EQUATION_TEXT,
            detail="equation claim has neither expression nor sympy text",
        )

    return _normalize_equation_text(source_text, bindings)


def structural_signature(claim: ConflictClaim) -> str | EquationFailure:
    normalization = canonicalize_equation(claim)
    if isinstance(normalization, EquationFailure):
        return normalization
    return normalization.structural_signature


def compare_equation_claims(claim_a: ConflictClaim, claim_b: ConflictClaim) -> EquationComparison:
    left = canonicalize_equation(claim_a)
    right = canonicalize_equation(claim_b)
    if isinstance(left, EquationFailure) or isinstance(right, EquationFailure):
        return EquationComparison(
            status=EquationComparisonStatus.INCOMPARABLE,
            left=left,
            right=right,
        )
    status = (
        EquationComparisonStatus.EQUIVALENT
        if left.canonical == right.canonical
        else EquationComparisonStatus.DIFFERENT
    )
    return EquationComparison(status=status, left=left, right=right)


def _claim_bindings(
    claim: ConflictClaim,
) -> tuple[EquationSymbolBinding, ...] | EquationFailure:
    if not claim.variables:
        return EquationFailure(
            code=EquationFailureCode.MISSING_VARIABLES,
            detail="equation claim has no declared symbol bindings",
        )

    bindings: list[EquationSymbolBinding] = []
    seen_symbols: set[str] = set()
    for variable in claim.variables:
        symbol = variable.symbol
        if not symbol:
            continue
        if symbol in seen_symbols:
            return EquationFailure(
                code=EquationFailureCode.PARSE_ERROR,
                detail=f"duplicate symbol binding: {symbol}",
            )
        seen_symbols.add(symbol)
        bindings.append(EquationSymbolBinding(
            symbol=symbol,
            concept_id=variable.concept_id,
            role=variable.role,
        ))
    if not bindings:
        return EquationFailure(
            code=EquationFailureCode.MISSING_VARIABLES,
            detail="equation claim has no declared symbol bindings",
        )
    return tuple(sorted(bindings, key=lambda binding: binding.symbol))


def _claim_source_text(claim: ConflictClaim) -> str | None:
    if isinstance(claim.expression, str) and claim.expression.strip():
        return claim.expression.strip()
    if isinstance(claim.sympy, str) and claim.sympy.strip():
        return claim.sympy.strip()
    return None


@lru_cache(maxsize=4096)
def _normalize_equation_text(
    source_text: str,
    bindings: tuple[EquationSymbolBinding, ...],
) -> EquationNormalization | EquationFailure:
    parsed = parse_equation(source_text, bindings)
    if isinstance(parsed, EquationFailure):
        return parsed
    return _normalize_parsed_equation(parsed)


def _normalize_parsed_equation(parsed: ParsedEquation) -> EquationNormalization | EquationFailure:
    sympy = _get_sympy()
    if sympy is None:
        return EquationFailure(
            code=EquationFailureCode.SYMPY_UNAVAILABLE,
            detail="sympy is not available",
        )
    lhs = _expr_to_sympy(parsed.lhs, sympy)
    rhs = _expr_to_sympy(parsed.rhs, sympy)
    diff = sympy.cancel(sympy.expand(lhs - rhs))
    structure = (
        ast_structural_signature(parsed.lhs)
        + " = "
        + ast_structural_signature(parsed.rhs)
    )
    return EquationNormalization(
        canonical=str(diff),
        source_text=parsed.source_text,
        structural_signature=structure,
    )


def _expr_to_sympy(expression: EquationExpr, sympy):
    if isinstance(expression, NumberExpr):
        return _sympy_number(expression.token, sympy)
    if isinstance(expression, SymbolExpr):
        return sympy.Symbol(expression.concept_id)
    if isinstance(expression, UnaryExpr):
        operand = _expr_to_sympy(expression.operand, sympy)
        return operand if expression.operator == "+" else -operand
    if isinstance(expression, BinaryExpr):
        left = _expr_to_sympy(expression.left, sympy)
        right = _expr_to_sympy(expression.right, sympy)
        if expression.operator == "+":
            return left + right
        if expression.operator == "-":
            return left - right
        if expression.operator == "*":
            return left * right
        if expression.operator == "/":
            return left / right
        if expression.operator == "^":
            return left**right
        raise ValueError(f"unsupported operator: {expression.operator}")
    if isinstance(expression, FunctionExpr):
        argument = _expr_to_sympy(expression.arguments[0], sympy)
        if expression.name in {"log", "ln"}:
            return sympy.log(argument)
        if expression.name == "exp":
            return sympy.exp(argument)
        if expression.name == "sqrt":
            return sympy.sqrt(argument)
        raise ValueError(f"unsupported function: {expression.name}")
    raise TypeError(f"unsupported expression: {expression!r}")


def _sympy_number(token: str, sympy):
    if "." in token or "e" in token.lower():
        return sympy.Rational(str(Decimal(token)))
    return sympy.Integer(int(token))


def _get_sympy():
    global _sympy
    if _sympy is None:
        try:
            import sympy as sympy_module
        except ImportError:
            _sympy = False
            return None
        _sympy = sympy_module
    if _sympy is False:
        return None
    return _sympy


__all__ = [
    "EquationComparison",
    "EquationComparisonStatus",
    "EquationFailure",
    "EquationFailureCode",
    "EquationNormalization",
    "canonicalize_equation",
    "compare_equation_claims",
    "equation_signature",
    "structural_signature",
]
