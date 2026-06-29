"""Numeric evaluation of parameterization relationships.

A parameterization edge carries a ``sympy`` expression relating an output concept
to its inputs. Evaluating it under concrete input values is a numeric-SymPy
operation, and propstore does not own a SymPy boundary: the ``human-to-sympy``
package does. This module is the thin propstore-side wrapper that delegates to
:func:`human_to_sympy.evaluate_numeric` and re-expresses its typed outcome as a
:class:`ParameterizationEvaluation`, plus the propstore-specific authored-handle
to-symbol alias rewrite (:func:`rewrite_parameterization_symbols`).

There is no direct ``import sympy`` here (CLAUDE.md substrate discipline: SymPy is
``human-to-sympy``'s boundary, not propstore's). The typed status set distinguishes
a value from each way evaluation declines to produce one, so callers never
collapse "missing input", "no solution", "non-numeric", and "unparseable" into
one overloaded ``None`` channel (honest ignorance, CLAUDE.md).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from human_to_sympy import NumericEvaluation, evaluate_numeric

_SAFE_SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ParameterizationEvaluationStatus(StrEnum):
    """How a parameterization evaluation resolved.

    All members except ``SYMPY_UNAVAILABLE`` mirror
    :class:`human_to_sympy.NumericEvaluationStatus` by value. ``SYMPY_UNAVAILABLE``
    is retained for callers that branch on it, but ``human-to-sympy`` hard-depends
    on SymPy, so :func:`evaluate_parameterization` never produces it.
    """

    VALUE = "value"
    SYMPY_UNAVAILABLE = "sympy_unavailable"
    INVALID_EXPRESSION = "invalid_expression"
    NON_NUMERIC = "non_numeric"
    MISSING_INPUT = "missing_input"
    NO_SOLUTION = "no_solution"


@dataclass(frozen=True)
class ParameterizationEvaluation:
    """The typed outcome of :func:`evaluate_parameterization`."""

    status: ParameterizationEvaluationStatus
    value: float | None = None
    detail: str | None = None

    @classmethod
    def from_value(cls, value: float) -> ParameterizationEvaluation:
        return cls(ParameterizationEvaluationStatus.VALUE, value=value)


def _status_from_numeric(evaluation: NumericEvaluation) -> ParameterizationEvaluationStatus:
    """Re-express a numeric-evaluation status in the parameterization vocabulary.

    The two status enums deliberately share the same value strings for every
    outcome ``human-to-sympy`` can return, so the package's status narrows
    directly to ours (the extra ``SYMPY_UNAVAILABLE`` member is propstore-only and
    never originates here).
    """

    return ParameterizationEvaluationStatus(evaluation.status.value)


def evaluate_parameterization(
    sympy_expr: str,
    input_values: Mapping[str, float],
    output_concept_id: str,
) -> ParameterizationEvaluation:
    """Evaluate a parameterization ``sympy`` expression under ``input_values``.

    Delegates to :func:`human_to_sympy.evaluate_numeric`, which handles both bare
    expressions and ``Eq(output, expr)`` forms and excludes ``output_concept_id``
    from the substituted inputs (a self-referencing relationship does not pin the
    value being solved for).
    """

    evaluation = evaluate_numeric(sympy_expr, dict(input_values), output_concept_id)
    return ParameterizationEvaluation(
        status=_status_from_numeric(evaluation),
        value=evaluation.value,
        detail=evaluation.detail,
    )


def rewrite_parameterization_symbols(
    sympy_expr: str,
    *,
    symbol_aliases: Mapping[str, Sequence[str]],
    symbol_targets: Mapping[str, str],
) -> str:
    """Rewrite authored parameterization symbols into caller-provided safe targets.

    Parameterization sympy strings often use local authored handles such as
    ``concept1`` or ``ca`` while runtime tables store canonical artifact ids.
    Callers provide alias candidates for each canonical concept id and a safe
    target symbol to substitute for that concept. This propstore-specific
    knowledge lives in the arguments, not in a wrapper layer (CLAUDE.md).
    """

    rewritten = sympy_expr
    placeholder_targets: dict[str, str] = {}
    placeholder_index = 0

    for concept_id, target_symbol in symbol_targets.items():
        aliases = symbol_aliases.get(concept_id, ())
        safe_aliases = [alias for alias in aliases if _SAFE_SYMBOL_RE.match(alias)]
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
