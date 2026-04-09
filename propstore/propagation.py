"""Shared SymPy evaluation for parameterization relationships.

Evaluates parameterization expressions given input values. Handles:
- Bare expressions (``a + b``) — direct substitution
- ``Eq(y, expr)`` — solve for y
- Self-referencing inputs (output concept in inputs) — exclude and solve
"""

from __future__ import annotations

import functools
import re
from collections.abc import Mapping, Sequence


_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@functools.lru_cache(maxsize=128)
def parse_cached(expr_str: str, symbol_names: tuple[str, ...]):
    from sympy import Symbol
    from sympy.parsing.sympy_parser import parse_expr

    symbols = {name: Symbol(name) for name in symbol_names}
    return parse_expr(expr_str, local_dict=symbols), symbols


def rewrite_parameterization_symbols(
    sympy_expr: str,
    *,
    symbol_aliases: Mapping[str, Sequence[str]],
    symbol_targets: Mapping[str, str],
) -> str:
    """Rewrite authored parameterization symbols into caller-provided safe targets.

    Parameterization sympy strings often use local authored handles such as
    ``concept1`` or ``ca`` while runtime tables store canonical artifact IDs.
    Callers provide alias candidates for each canonical concept ID and a safe
    target symbol to substitute for that concept.
    """
    rewritten = sympy_expr
    placeholder_targets: dict[str, str] = {}
    placeholder_index = 0

    for concept_id, target_symbol in symbol_targets.items():
        aliases = symbol_aliases.get(concept_id, ())
        safe_aliases = [
            alias
            for alias in aliases
            if isinstance(alias, str) and _SAFE_SYMBOL_RE.match(alias)
        ]
        if not safe_aliases:
            continue

        placeholder = f"__psym_{placeholder_index}__"
        placeholder_index += 1
        placeholder_targets[placeholder] = target_symbol

        for alias in sorted(dict.fromkeys(safe_aliases), key=len, reverse=True):
            rewritten = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
                placeholder,
                rewritten,
            )

    for placeholder, target_symbol in placeholder_targets.items():
        rewritten = rewritten.replace(placeholder, target_symbol)

    return rewritten


def evaluate_parameterization(
    sympy_expr: str,
    input_values: dict[str, float],
    output_concept_id: str,
) -> float | None:
    """Evaluate a SymPy parameterization expression.

    Returns the computed float value, or None if evaluation fails
    (missing inputs, unsolvable expression, etc.).
    """
    try:
        from sympy import Equality, Symbol, solve
    except ImportError:
        return None

    # Build symbol names from inputs + output
    all_names = set(input_values.keys()) | {output_concept_id}
    parsed_expr, symbols = parse_cached(sympy_expr, tuple(sorted(all_names)))

    # Filter input_values to exclude the output concept (self-referencing)
    effective_inputs = {k: v for k, v in input_values.items() if k != output_concept_id}

    try:
        if isinstance(parsed_expr, Equality):
            # Eq(y, expr) form — solve for output
            output_sym = symbols.get(output_concept_id)
            if output_sym is None:
                output_sym = Symbol(output_concept_id)

            subs_pairs = [(symbols[k], v) for k, v in effective_inputs.items() if k in symbols]
            substituted = parsed_expr.subs(subs_pairs)
            solutions = solve(substituted, output_sym)
            if solutions:
                return float(solutions[0])
            return None
        else:
            # Bare expression — direct substitution
            subs_pairs = [(symbols[k], v) for k, v in effective_inputs.items() if k in symbols]
            result = parsed_expr.subs(subs_pairs)
            return float(result)
    except (TypeError, ValueError, ZeroDivisionError, AttributeError):
        return None
