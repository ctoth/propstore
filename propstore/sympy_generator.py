"""Auto-generate SymPy expressions from human-readable math strings.

Used by the claim validator and sidecar builder to provide machine-parseable
equation representations for equation claims that only have a human-readable
`expression` field.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
import logging
from tokenize import TokenError

from sympy import Symbol, SympifyError
from sympy.parsing.sympy_parser import parse_expr


# Symbols that SymPy recognizes as constants — don't warn about these
_SYMPY_CONSTANTS = {"pi", "E", "I", "oo", "zoo", "nan"}

# SymPy built-in function names that collide with common variable names.
# parse_expr without local_dict interprets these as FunctionClass objects,
# causing TypeError on arithmetic (e.g., beta * x fails).
_IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*")
# Names that should remain as SymPy functions/constants, not be overridden
_SYMPY_BUILTINS = {
    "Eq", "exp", "log", "ln", "sqrt", "sin", "cos", "tan", "asin", "acos",
    "atan", "atan2", "sinh", "cosh", "tanh", "Sum", "Product", "Integral",
    "Derivative", "Abs", "Mod", "ceiling", "floor", "sign", "Piecewise",
    "Max", "Min", "re", "im", "conjugate", "Rational", "Float", "Integer",
    "Symbol", "symbols", "Function", "Norm",
    "pi", "E", "I", "oo", "zoo", "nan",
    "true", "false", "True", "False", "None",
}


def _build_local_dict(text: str) -> dict[str, Symbol]:
    """Extract identifiers from expression text and declare them as Symbols.

    This prevents SymPy from interpreting identifiers like 'beta', 'gamma',
    'zeta' as built-in special functions.
    """
    names = set(_IDENTIFIER_RE.findall(text)) - _SYMPY_BUILTINS
    return {name: Symbol(name) for name in names}


@dataclass(frozen=True)
class SympyGenerationResult:
    expression: str | None
    error: str | None


def generate_sympy_with_error(expression: str | None) -> SympyGenerationResult:
    """Generate a SymPy expression and preserve the failure reason."""
    if not expression or not isinstance(expression, str):
        return SympyGenerationResult(None, "missing expression")

    text = expression.strip()
    if not text:
        return SympyGenerationResult(None, "empty expression")

    # Preprocess: replace ^ with **
    text = text.replace("^", "**")

    # If contains =, take the RHS
    if "=" in text:
        parts = text.split("=", 1)
        text = parts[1].strip()

    if not text:
        return SympyGenerationResult(None, "expression has no right-hand side")

    try:
        result = parse_expr(text, local_dict=_build_local_dict(text))
        return SympyGenerationResult(str(result), None)
    except (SympifyError, TypeError, ValueError, SyntaxError, TokenError) as exc:
        logging.warning("SymPy parse_expr failed for %r: %s", text, exc)
        return SympyGenerationResult(None, str(exc))


def generate_sympy(expression: str | None) -> str | None:
    """Generate a SymPy-parseable string from a human-readable math expression.

    Args:
        expression: Human-readable math string (e.g., "Fa = 1 / (2 * pi * Ta)")

    Returns:
        SymPy-parseable string of the RHS, or None if parsing fails.
    """
    return generate_sympy_with_error(expression).expression


def check_symbols(
    expression: str,
    variables: list[dict],
) -> list[str]:
    """Check that all free symbols in an expression are accounted for in the variables list.

    Args:
        expression: Human-readable math string
        variables: List of variable binding dicts, each with at least a 'symbol' key

    Returns:
        List of warning strings for symbols not in the variables list.
    """
    text = expression.strip()
    if not text:
        return []

    # Preprocess
    text = text.replace("^", "**")
    if "=" in text:
        parts = text.split("=", 1)
        text = parts[1].strip()

    if not text:
        return []

    try:
        expr = parse_expr(text, local_dict=_build_local_dict(text))
    except (SympifyError, SyntaxError, TypeError, ValueError):
        return []

    free = {str(s) for s in expr.free_symbols}

    # Remove SymPy built-in constants
    free -= _SYMPY_CONSTANTS

    # Build set of declared symbols
    declared = {v.get("symbol", "") for v in variables if isinstance(v, dict)}

    warnings = []
    for sym in sorted(free - declared):
        warnings.append(f"Symbol '{sym}' in expression is not in variables list")

    return warnings
