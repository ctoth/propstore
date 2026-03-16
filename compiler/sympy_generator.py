"""Auto-generate SymPy expressions from human-readable math strings.

Used by the claim validator and sidecar builder to provide machine-parseable
equation representations for equation claims that only have a human-readable
`expression` field.
"""

from __future__ import annotations

from dataclasses import dataclass

from sympy import SympifyError
from sympy.parsing.sympy_parser import parse_expr


# Symbols that SymPy recognizes as constants — don't warn about these
_SYMPY_CONSTANTS = {"pi", "E", "I", "oo", "zoo", "nan"}


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
        result = parse_expr(text)
        return SympyGenerationResult(str(result), None)
    except (SympifyError, SyntaxError, TypeError, ValueError) as exc:
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
        expr = parse_expr(text)
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
