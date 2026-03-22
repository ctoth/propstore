"""Equation canonicalization and signature helpers.

Extracted from conflict_detector.py — provides SymPy-based equation
normalization for equivalence checking and canonical signature building
for grouping equations by their variable structure.
"""

from __future__ import annotations

from typing import Any


def equation_signature(claim: dict) -> tuple[str, tuple[str, ...]] | None:
    """Build a canonical signature for an equation claim for grouping.

    Returns (dependent_concept, (sorted independent concepts...)) or None
    if the claim doesn't have the expected variable structure.
    """
    variables = claim.get("variables")
    if not isinstance(variables, list):
        return None

    dependent_concepts: list[str] = []
    for var in variables:
        if isinstance(var, dict) and var.get("role") == "dependent":
            c = var.get("concept")
            if isinstance(c, str) and c:
                dependent_concepts.append(c)
    if len(dependent_concepts) != 1:
        return None

    dependent_concept = dependent_concepts[0]
    independent_list: list[str] = []
    for var in variables:
        if isinstance(var, dict):
            c = var.get("concept")
            if isinstance(c, str) and c and c != dependent_concept:
                independent_list.append(c)
    independents = sorted(independent_list)
    return dependent_concept, tuple(independents)


def canonicalize_equation(claim: dict) -> str | None:
    """Canonicalize an equation claim using SymPy for equivalence checking.

    Returns a canonical string representation of the equation (as simplified
    lhs - rhs), or None if parsing fails or SymPy is unavailable.
    """
    try:
        from tokenize import TokenError

        from sympy import Equality, SympifyError, Symbol, simplify
        from sympy.parsing.sympy_parser import parse_expr
    except ImportError:
        return None

    variables = claim.get("variables")
    if not isinstance(variables, list):
        return None

    symbol_map = {}
    for var in variables:
        if not isinstance(var, dict):
            continue
        symbol = var.get("symbol")
        concept_id = var.get("concept")
        if isinstance(symbol, str) and symbol and isinstance(concept_id, str) and concept_id:
            symbol_map[symbol] = Symbol(concept_id)
    if not symbol_map:
        return None

    explicit_sympy = claim.get("sympy")
    if isinstance(explicit_sympy, str) and explicit_sympy.strip():
        text = explicit_sympy.strip().replace("^", "**")
        try:
            parsed = parse_expr(text, local_dict=symbol_map)
            if isinstance(parsed, Equality):
                lhs_val: Any = parsed.lhs
                rhs_val: Any = parsed.rhs
                return str(simplify(lhs_val - rhs_val))
        except (SympifyError, SyntaxError, TypeError, ValueError):
            pass

    expression = claim.get("expression")
    if not isinstance(expression, str) or "=" not in expression:
        return None

    lhs_text, rhs_text = expression.replace("^", "**").split("=", 1)
    try:
        lhs = parse_expr(lhs_text.strip(), local_dict=symbol_map)
        rhs = parse_expr(rhs_text.strip(), local_dict=symbol_map)
    except (SympifyError, SyntaxError, TypeError, ValueError, AttributeError, TokenError):
        return None
    diff_expr: Any = lhs - rhs
    return str(simplify(diff_expr))
