"""Shared SymPy evaluation for parameterization relationships.

Evaluates parameterization expressions given input values. Handles:
- Bare expressions (``a + b``) — direct substitution
- ``Eq(y, expr)`` — solve for y
- Self-referencing inputs (output concept in inputs) — exclude and solve
"""

from __future__ import annotations

import functools
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ParameterizationEvaluationStatus(StrEnum):
    VALUE = "value"
    SYMPY_UNAVAILABLE = "sympy_unavailable"
    INVALID_EXPRESSION = "invalid_expression"
    MISSING_INPUT = "missing_input"
    NO_SOLUTION = "no_solution"
    NON_NUMERIC = "non_numeric"


@dataclass(frozen=True)
class ParameterizationEvaluation:
    status: ParameterizationEvaluationStatus
    value: float | None = None
    detail: str | None = None

    @classmethod
    def from_value(cls, value: float) -> ParameterizationEvaluation:
        return cls(ParameterizationEvaluationStatus.VALUE, value=value)


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
) -> ParameterizationEvaluation:
    """Evaluate a SymPy parameterization expression.

    Returns a typed result so callers do not collapse missing inputs,
    unsolved equations, parse failures, and non-numeric results into one
    overloaded ``None`` channel.
    """
    try:
        from sympy import Equality, Symbol, solve
    except ImportError:
        return ParameterizationEvaluation(
            ParameterizationEvaluationStatus.SYMPY_UNAVAILABLE,
            detail="sympy import failed",
        )

    # Build symbol names from inputs + output
    all_names = set(input_values.keys()) | {output_concept_id}
    try:
        parsed_expr, symbols = parse_cached(sympy_expr, tuple(sorted(all_names)))
    except (TypeError, ValueError, SyntaxError, AttributeError) as exc:
        return ParameterizationEvaluation(
            ParameterizationEvaluationStatus.INVALID_EXPRESSION,
            detail=str(exc),
        )

    # Filter input_values to exclude the output concept (self-referencing)
    effective_inputs = {k: v for k, v in input_values.items() if k != output_concept_id}

    def _numeric_result(value: Any) -> ParameterizationEvaluation:
        try:
            numeric = float(value)
        except (TypeError, ValueError, ZeroDivisionError, AttributeError) as exc:
            return ParameterizationEvaluation(
                ParameterizationEvaluationStatus.NON_NUMERIC,
                detail=str(exc),
            )
        if not math.isfinite(numeric):
            return ParameterizationEvaluation(
                ParameterizationEvaluationStatus.NON_NUMERIC,
                detail=repr(value),
            )
        return ParameterizationEvaluation.from_value(numeric)

    try:
        if isinstance(parsed_expr, Equality):
            # Eq(y, expr) form — solve for output
            output_sym = symbols.get(output_concept_id)
            if output_sym is None:
                output_sym = Symbol(output_concept_id)

            subs_pairs = [(symbols[k], v) for k, v in effective_inputs.items() if k in symbols]
            substituted = parsed_expr.subs(subs_pairs)
            missing_symbols = substituted.free_symbols - {output_sym}
            if missing_symbols:
                return ParameterizationEvaluation(
                    ParameterizationEvaluationStatus.MISSING_INPUT,
                    detail=", ".join(sorted(str(symbol) for symbol in missing_symbols)),
                )
            solutions = solve(substituted, output_sym)
            if solutions:
                return _numeric_result(solutions[0])
            return ParameterizationEvaluation(ParameterizationEvaluationStatus.NO_SOLUTION)
        else:
            # Bare expression — direct substitution
            subs_pairs = [(symbols[k], v) for k, v in effective_inputs.items() if k in symbols]
            result = parsed_expr.subs(subs_pairs)
            if result.free_symbols:
                return ParameterizationEvaluation(
                    ParameterizationEvaluationStatus.MISSING_INPUT,
                    detail=", ".join(sorted(str(symbol) for symbol in result.free_symbols)),
                )
            return _numeric_result(result)
    except (TypeError, ValueError, ZeroDivisionError, AttributeError) as exc:
        return ParameterizationEvaluation(
            ParameterizationEvaluationStatus.INVALID_EXPRESSION,
            detail=str(exc),
        )
