"""Typed equation normalization and structural comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence

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
    residual: object | None = None
    domain_sensitive: bool = False


class EquationComparisonStatus(StrEnum):
    """Equation comparison outcome.

    INCOMPARABLE is reserved for parse/normalization failures. UNKNOWN means
    both equations parsed, but the available algebraic procedure cannot make a
    sound equivalence/difference decision under the declared domain.
    """

    EQUIVALENT = "equivalent"
    DIFFERENT = "different"
    INCOMPARABLE = "incomparable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EquationComparison:
    status: EquationComparisonStatus
    left: EquationNormalization | EquationFailure
    right: EquationNormalization | EquationFailure


@dataclass(frozen=True)
class DomainAssumption:
    symbol: str


@dataclass(frozen=True)
class Real(DomainAssumption):
    pass


@dataclass(frozen=True)
class Positive(DomainAssumption):
    pass


@dataclass(frozen=True)
class NonNegative(DomainAssumption):
    pass


@dataclass(frozen=True)
class Integer(DomainAssumption):
    pass


_sympy = None


def equation_signature(claim: ConflictClaim) -> tuple[str, tuple[str, ...]] | None:
    """Build a concept-based grouping signature for typed equation claims."""
    concept_ids = sorted(
        {
            variable.concept_id
            for variable in claim.variables
            if variable.concept_id
        }
    )
    if not concept_ids:
        return None
    return concept_ids[0], tuple(concept_ids[1:])


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


def compare_equation_claims(
    claim_a: ConflictClaim,
    claim_b: ConflictClaim,
    *,
    domain_assumptions: Sequence[DomainAssumption] = (),
) -> EquationComparison:
    assumptions = tuple(domain_assumptions)
    left = _canonicalize_equation(claim_a, assumptions)
    right = _canonicalize_equation(claim_b, assumptions)
    if isinstance(left, EquationFailure) or isinstance(right, EquationFailure):
        return EquationComparison(
            status=EquationComparisonStatus.INCOMPARABLE,
            left=left,
            right=right,
        )
    status = _compare_normalizations(left, right, assumptions)
    return EquationComparison(status=status, left=left, right=right)


def _canonicalize_equation(
    claim: ConflictClaim,
    domain_assumptions: tuple[DomainAssumption, ...],
) -> EquationNormalization | EquationFailure:
    bindings = _claim_bindings(claim)
    if isinstance(bindings, EquationFailure):
        return bindings

    source_text = _claim_source_text(claim)
    if source_text is None:
        return EquationFailure(
            code=EquationFailureCode.MISSING_EQUATION_TEXT,
            detail="equation claim has neither expression nor sympy text",
        )

    return _normalize_equation_text(source_text, bindings, domain_assumptions)


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
    domain_assumptions: tuple[DomainAssumption, ...] = (),
) -> EquationNormalization | EquationFailure:
    parsed = parse_equation(source_text, bindings)
    if isinstance(parsed, EquationFailure):
        return parsed
    return _normalize_parsed_equation(parsed, domain_assumptions)


def _normalize_parsed_equation(
    parsed: ParsedEquation,
    domain_assumptions: tuple[DomainAssumption, ...] = (),
) -> EquationNormalization | EquationFailure:
    sympy = _get_sympy()
    if sympy is None:
        return EquationFailure(
            code=EquationFailureCode.SYMPY_UNAVAILABLE,
            detail="sympy is not available",
        )
    assumptions = _domain_assumptions_by_symbol(domain_assumptions)
    lhs = _expr_to_sympy(parsed.lhs, sympy, assumptions)
    rhs = _expr_to_sympy(parsed.rhs, sympy, assumptions)
    raw_diff = lhs - rhs
    domain_sensitive = _has_domain_sensitive_functions(raw_diff, sympy)
    diff = _simplify_residual(raw_diff, sympy, domain_assumptions)
    canonical = _canonical_residual(diff, sympy)
    structure = (
        ast_structural_signature(parsed.lhs)
        + " = "
        + ast_structural_signature(parsed.rhs)
    )
    return EquationNormalization(
        canonical=canonical,
        source_text=parsed.source_text,
        structural_signature=structure,
        residual=diff,
        domain_sensitive=domain_sensitive,
    )


def _expr_to_sympy(
    expression: EquationExpr,
    sympy,
    assumptions: dict[str, dict[str, bool]],
):
    if isinstance(expression, NumberExpr):
        return _sympy_number(expression.token, sympy)
    if isinstance(expression, SymbolExpr):
        symbol_assumptions = assumptions.get(expression.symbol)
        if symbol_assumptions is None:
            symbol_assumptions = assumptions.get(expression.concept_id, {})
        return sympy.Symbol(expression.concept_id, **symbol_assumptions)
    if isinstance(expression, UnaryExpr):
        operand = _expr_to_sympy(expression.operand, sympy, assumptions)
        return operand if expression.operator == "+" else -operand
    if isinstance(expression, BinaryExpr):
        left = _expr_to_sympy(expression.left, sympy, assumptions)
        right = _expr_to_sympy(expression.right, sympy, assumptions)
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
        argument = _expr_to_sympy(expression.arguments[0], sympy, assumptions)
        if expression.name == "abs":
            return sympy.Abs(argument)
        if expression.name in {"log", "ln"}:
            return sympy.log(argument)
        if expression.name == "exp":
            return sympy.exp(argument)
        if expression.name == "sqrt":
            return sympy.sqrt(argument)
        raise ValueError(f"unsupported function: {expression.name}")
    raise TypeError(f"unsupported expression: {expression!r}")


def _domain_assumptions_by_symbol(
    assumptions: tuple[DomainAssumption, ...],
) -> dict[str, dict[str, bool]]:
    result: dict[str, dict[str, bool]] = {}
    for assumption in assumptions:
        values = result.setdefault(assumption.symbol, {"finite": True})
        if isinstance(assumption, Positive):
            values.update({"positive": True, "real": True})
        elif isinstance(assumption, NonNegative):
            values.update({"nonnegative": True, "real": True})
        elif isinstance(assumption, Integer):
            values.update({"integer": True, "real": True})
        elif isinstance(assumption, Real):
            values.update({"real": True})
    return result


def _simplify_residual(expr, sympy, assumptions: tuple[DomainAssumption, ...]):
    simplified = sympy.powsimp(expr, force=bool(assumptions))
    simplified = sympy.logcombine(simplified, force=bool(assumptions))
    return sympy.simplify(sympy.cancel(sympy.expand(simplified)))


def _canonical_residual(expr, sympy) -> str:
    expr = sympy.cancel(sympy.expand(expr))
    symbols = sorted(expr.free_symbols, key=lambda symbol: str(symbol))
    if symbols:
        try:
            poly = sympy.Poly(expr, *symbols)
        except sympy.PolynomialError:
            return min(str(expr), str(-expr))
        _content, primitive = poly.primitive()
        expr = primitive.as_expr()
    terms = expr.as_ordered_terms()
    if terms and terms[0].could_extract_minus_sign():
        expr = -expr
    return str(expr)


def _compare_normalizations(
    left: EquationNormalization,
    right: EquationNormalization,
    assumptions: tuple[DomainAssumption, ...],
) -> EquationComparisonStatus:
    if left.canonical == right.canonical:
        if not assumptions and (left.domain_sensitive or right.domain_sensitive):
            return EquationComparisonStatus.UNKNOWN
        return EquationComparisonStatus.EQUIVALENT
    sympy = _get_sympy()
    if sympy is None or left.residual is None or right.residual is None:
        return EquationComparisonStatus.UNKNOWN
    delta = _simplify_residual(left.residual - right.residual, sympy, assumptions)
    if delta == 0:
        if not assumptions and (left.domain_sensitive or right.domain_sensitive):
            return EquationComparisonStatus.UNKNOWN
        return EquationComparisonStatus.EQUIVALENT
    if not assumptions and (left.domain_sensitive or right.domain_sensitive):
        positive_assumptions = tuple(
            Positive(str(symbol)) for symbol in sorted(delta.free_symbols, key=str)
        )
        positive_delta = _simplify_residual(
            _with_positive_symbols(left.residual - right.residual, sympy),
            sympy,
            positive_assumptions,
        )
        if positive_delta == 0:
            return EquationComparisonStatus.UNKNOWN
        return EquationComparisonStatus.DIFFERENT
    if assumptions:
        return EquationComparisonStatus.DIFFERENT
    if _is_polynomial(delta, sympy):
        return EquationComparisonStatus.DIFFERENT
    return EquationComparisonStatus.UNKNOWN


def _has_domain_sensitive_functions(expr, sympy) -> bool:
    return bool(expr.atoms(sympy.Function))


def _with_positive_symbols(expr, sympy):
    replacements = {
        symbol: sympy.Symbol(str(symbol), positive=True, finite=True)
        for symbol in expr.free_symbols
    }
    return expr.xreplace(replacements)


def _is_polynomial(expr, sympy) -> bool:
    symbols = sorted(expr.free_symbols, key=lambda symbol: str(symbol))
    if not symbols:
        return True
    try:
        sympy.Poly(expr, *symbols)
    except sympy.PolynomialError:
        return False
    return True


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
    "Integer",
    "NonNegative",
    "Positive",
    "Real",
    "canonicalize_equation",
    "compare_equation_claims",
    "equation_signature",
    "structural_signature",
]
