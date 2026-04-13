"""Equation canonicalization and signature helpers.

Extracted from conflict_detector.py — provides SymPy-based equation
normalization for equivalence checking and canonical signature building
for grouping equations by their variable structure.
"""

from __future__ import annotations

import re
from typing import Any

# Reject equation strings that contain Python code-execution patterns.
# This is defense-in-depth: parse_expr's local_dict alone does NOT
# prevent __import__('os').system() from executing (the name resolves
# via Python builtins, not the local_dict).
_INJECTION_RE = re.compile(
    r"__\w+__|(?<!\w)(?:import|eval|exec|compile|open|getattr|setattr|delattr)\s*\(",
    re.IGNORECASE,
)


def _reject_injection(text: str) -> None:
    """Raise ValueError if *text* contains code-execution patterns."""
    if _INJECTION_RE.search(text):
        raise ValueError(f"equation contains forbidden pattern: {text!r}")


def equation_signature(claim: object) -> tuple[str, tuple[str, ...]] | None:
    """Build a canonical signature for an equation claim for grouping.

    Returns (dependent_concept, (sorted independent concepts...)) or None
    if the claim doesn't have the expected variable structure.
    """
    variables = _claim_field(claim, "variables")
    if not isinstance(variables, (list, tuple)):
        return None

    dependent_concepts: list[str] = []
    for var in variables:
        if _variable_field(var, "role") == "dependent":
            concept_id = _variable_field(var, "concept")
            if isinstance(concept_id, str) and concept_id:
                dependent_concepts.append(concept_id)
    if len(dependent_concepts) != 1:
        return None

    dependent_concept = dependent_concepts[0]
    independent_list: list[str] = []
    for var in variables:
        concept_id = _variable_field(var, "concept")
        if isinstance(concept_id, str) and concept_id and concept_id != dependent_concept:
            independent_list.append(concept_id)
    independents = sorted(independent_list)
    return dependent_concept, tuple(independents)


def canonicalize_equation(claim: object) -> str | None:
    """Canonicalize an equation claim using SymPy for equivalence checking.

    Returns a canonical string representation of the equation (as simplified
    lhs - rhs), or None if parsing fails or SymPy is unavailable.
    """
    try:
        from tokenize import TokenError

        from sympy import Equality, SympifyError, Symbol, simplify
        from sympy.parsing.sympy_parser import (
            implicit_multiplication,
            parse_expr,
            standard_transformations,
        )
    except ImportError:
        return None

    variables = _claim_field(claim, "variables")
    if not isinstance(variables, (list, tuple)):
        return None

    symbol_map = {}
    for var in variables:
        symbol = _variable_field(var, "symbol")
        concept_id = _variable_field(var, "concept")
        if isinstance(symbol, str) and symbol and isinstance(concept_id, str) and concept_id:
            symbol_map[symbol] = Symbol(concept_id)
    if not symbol_map:
        return None

    explicit_sympy = _claim_field(claim, "sympy")
    if isinstance(explicit_sympy, str) and explicit_sympy.strip():
        text = explicit_sympy.strip().replace("^", "**")
        try:
            _reject_injection(text)
            parsed = parse_expr(text, local_dict=symbol_map)
            if isinstance(parsed, Equality):
                lhs_val: Any = parsed.lhs
                rhs_val: Any = parsed.rhs
                return str(simplify(lhs_val - rhs_val))
        except (SympifyError, SyntaxError, TypeError, ValueError):
            pass

    expression = _claim_field(claim, "expression")
    if not isinstance(expression, str) or "=" not in expression:
        return None

    _safe_transforms = standard_transformations + (implicit_multiplication,)

    lhs_text, rhs_text = expression.replace("^", "**").split("=", 1)
    try:
        _reject_injection(lhs_text)
        _reject_injection(rhs_text)
        lhs = parse_expr(
            lhs_text.strip(),
            local_dict=symbol_map,
            transformations=_safe_transforms,
            evaluate=False,
        )
        rhs = parse_expr(
            rhs_text.strip(),
            local_dict=symbol_map,
            transformations=_safe_transforms,
            evaluate=False,
        )
    except (SympifyError, SyntaxError, TypeError, ValueError, AttributeError, TokenError):
        return None
    diff_expr: Any = lhs - rhs
    return str(simplify(diff_expr))


def _claim_field(claim: object, key: str) -> Any:
    getter = getattr(claim, "get", None)
    if callable(getter):
        return getter(key)
    return getattr(claim, key, None)


def _variable_field(variable: object, key: str) -> Any:
    getter = getattr(variable, "get", None)
    if callable(getter):
        return getter(key)
    if key == "concept":
        return getattr(variable, "concept_id", None)
    return getattr(variable, key, None)
