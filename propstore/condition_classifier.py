"""Condition classification for the propstore conflict detector.

Classifies pairs of condition sets as CONFLICT, PHI_NODE, or OVERLAP
using Z3 as the primary path (when available) and interval arithmetic
as the fallback.

Entry point: classify_conditions(conditions_a, conditions_b, cel_registry)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING

from propstore.cel_checker import ConceptInfo
from propstore.conflict_detector.models import ConflictClass

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver


# ── Regex constants ───────────────────────────────────────────────────

_NUMERIC_CONDITION_RE = re.compile(
    r"^\s*(?P<name>\w+)\s*(?P<op><=|>=|==|!=|<|>)\s*(?P<value>-?\d+(?:\.\d+)?)\s*$"
)
_STRING_CONDITION_RE = re.compile(
    r"""^\s*(?P<name>\w+)\s*(?P<op>==|!=)\s*(?P<quote>['"])(?P<value>.+?)(?P=quote)\s*$"""
)
_BOOLEAN_CONDITION_RE = re.compile(
    r"^\s*(?P<name>\w+)\s*(?P<op>==|!=)\s*(?P<value>true|false)\s*$",
    re.IGNORECASE,
)


# ── Dataclasses ───────────────────────────────────────────────────────


@dataclass
class _NumericConstraint:
    lower: float | None = None
    lower_inclusive: bool = False
    upper: float | None = None
    upper_inclusive: bool = False
    equals: float | None = None
    excluded: set[float] = dataclass_field(default_factory=set)


@dataclass
class _DiscreteConstraint:
    equals: str | bool | None = None
    excluded: set[str | bool] = dataclass_field(default_factory=set)


@dataclass
class _ConditionSummary:
    numeric: dict[str, _NumericConstraint]
    discrete: dict[str, _DiscreteConstraint]


# ── Z3 condition classification ──────────────────────────────────────


def _try_z3_classify(
    conditions_a: list[str],
    conditions_b: list[str],
    cel_registry: dict[str, ConceptInfo] | None,
    solver: Z3ConditionSolver | None = None,
) -> ConflictClass | None:
    """Try to classify conditions using Z3. Returns None if Z3 unavailable."""
    if solver is None:
        if cel_registry is None:
            return None
        try:
            from propstore.z3_conditions import Z3ConditionSolver
        except ImportError:
            return None
        solver = Z3ConditionSolver(cel_registry)
    import z3
    from propstore.z3_conditions import Z3TranslationError
    try:
        if solver.are_equivalent(conditions_a, conditions_b):
            return ConflictClass.CONFLICT
        if solver.are_disjoint(conditions_a, conditions_b):
            return ConflictClass.PHI_NODE
    except (z3.Z3Exception, Z3TranslationError) as exc:
        logging.warning("Z3 condition classification failed: %s", exc)
        return None  # Z3 failed — fall through to fallback
    return ConflictClass.OVERLAP


# ── Condition classification ─────────────────────────────────────────


def classify_conditions(
    conditions_a: list[str],
    conditions_b: list[str],
    cel_registry: dict[str, ConceptInfo] | None = None,
    *,
    solver: Z3ConditionSolver | None = None,
) -> ConflictClass:
    """Classify a pair of differing-value claims based on their conditions.

    Returns CONFLICT, PHI_NODE, or OVERLAP.

    Z3 is the primary path when cel_registry is provided. Existing interval
    arithmetic is the fallback when Z3 isn't installed or fails.
    """
    normalized_a = sorted(conditions_a)
    normalized_b = sorted(conditions_b)
    if normalized_a == normalized_b:
        # Identical conditions (or both empty) -> CONFLICT
        return ConflictClass.CONFLICT

    # Primary path: Z3
    z3_result = _try_z3_classify(
        conditions_a,
        conditions_b,
        cel_registry,
        solver=solver,
    )
    if z3_result is not None:
        return z3_result

    # Fallback: interval arithmetic
    summary_a = _summarize_conditions(conditions_a)
    summary_b = _summarize_conditions(conditions_b)
    if summary_a is not None and summary_b is not None:
        if summary_a == summary_b:
            return ConflictClass.CONFLICT
        if _conditions_disjoint(summary_a, summary_b):
            return ConflictClass.PHI_NODE
        return ConflictClass.OVERLAP

    # Last resort: conditions couldn't be parsed into summaries.
    # String-set disjointness does NOT prove region disjointness —
    # e.g. "F1/F0 > 3.0" and "F1/F0 > 2.0" are string-disjoint but
    # their regions overlap.  Conservative: return OVERLAP.
    return ConflictClass.OVERLAP


# ── Condition parsing helpers ─────────────────────────────────────────


def _parse_condition_atom(
    condition: str,
) -> tuple[str, str, float | str | bool, str] | None:
    numeric_match = _NUMERIC_CONDITION_RE.match(condition)
    if numeric_match:
        return (
            numeric_match.group("name"),
            numeric_match.group("op"),
            float(numeric_match.group("value")),
            "numeric",
        )

    string_match = _STRING_CONDITION_RE.match(condition)
    if string_match:
        return (
            string_match.group("name"),
            string_match.group("op"),
            string_match.group("value"),
            "discrete",
        )

    boolean_match = _BOOLEAN_CONDITION_RE.match(condition)
    if boolean_match:
        return (
            boolean_match.group("name"),
            boolean_match.group("op"),
            boolean_match.group("value").lower() == "true",
            "discrete",
        )

    return None


def _summarize_conditions(conditions: list[str]) -> _ConditionSummary | None:
    summary = _ConditionSummary(numeric={}, discrete={})
    for condition in conditions:
        parsed = _parse_condition_atom(condition)
        if parsed is None:
            return None
        name, op, value, value_kind = parsed
        if value_kind == "numeric":
            constraint = summary.numeric.setdefault(name, _NumericConstraint())
            if not isinstance(value, (int, float)):
                return None
            value = float(value)
            if op == "==":
                constraint.equals = value
                constraint.lower = value
                constraint.upper = value
                constraint.lower_inclusive = True
                constraint.upper_inclusive = True
            elif op == "!=":
                constraint.excluded.add(value)
            elif op == ">":
                if constraint.lower is None or value > constraint.lower or (
                    value == constraint.lower and constraint.lower_inclusive
                ):
                    constraint.lower = value
                    constraint.lower_inclusive = False
            elif op == ">=":
                if constraint.lower is None or value > constraint.lower or (
                    value == constraint.lower and not constraint.lower_inclusive
                ):
                    constraint.lower = value
                    constraint.lower_inclusive = True
            elif op == "<":
                if constraint.upper is None or value < constraint.upper or (
                    value == constraint.upper and constraint.upper_inclusive
                ):
                    constraint.upper = value
                    constraint.upper_inclusive = False
            elif op == "<=":
                if constraint.upper is None or value < constraint.upper or (
                    value == constraint.upper and not constraint.upper_inclusive
                ):
                    constraint.upper = value
                    constraint.upper_inclusive = True
        else:
            constraint = summary.discrete.setdefault(name, _DiscreteConstraint())
            if not isinstance(value, (str, bool)):
                return None
            if op == "==":
                constraint.equals = value
            elif op == "!=":
                constraint.excluded.add(value)
    return summary


def _numeric_constraints_disjoint(
    left: _NumericConstraint,
    right: _NumericConstraint,
) -> bool:
    if left.equals is not None and right.equals is not None:
        return left.equals != right.equals
    if left.equals is not None:
        return _numeric_value_excluded(left.equals, right)
    if right.equals is not None:
        return _numeric_value_excluded(right.equals, left)

    lower, lower_inclusive = _max_lower_bound(left, right)
    upper, upper_inclusive = _min_upper_bound(left, right)
    if lower is not None and upper is not None:
        if lower > upper:
            return True
        if lower == upper and not (lower_inclusive and upper_inclusive):
            return True
        if lower == upper and (lower in left.excluded or lower in right.excluded):
            return True
    return False


def _numeric_value_excluded(value: float, constraint: _NumericConstraint) -> bool:
    if constraint.lower is not None:
        if value < constraint.lower:
            return True
        if value == constraint.lower and not constraint.lower_inclusive:
            return True
    if constraint.upper is not None:
        if value > constraint.upper:
            return True
        if value == constraint.upper and not constraint.upper_inclusive:
            return True
    return value in constraint.excluded


def _max_lower_bound(
    left: _NumericConstraint,
    right: _NumericConstraint,
) -> tuple[float | None, bool]:
    candidates = []
    if left.lower is not None:
        candidates.append((left.lower, left.lower_inclusive))
    if right.lower is not None:
        candidates.append((right.lower, right.lower_inclusive))
    if not candidates:
        return None, False
    lower, inclusive = candidates[0]
    for value, candidate_inclusive in candidates[1:]:
        if value > lower:
            lower, inclusive = value, candidate_inclusive
        elif value == lower:
            inclusive = inclusive and candidate_inclusive
    return lower, inclusive


def _min_upper_bound(
    left: _NumericConstraint,
    right: _NumericConstraint,
) -> tuple[float | None, bool]:
    candidates = []
    if left.upper is not None:
        candidates.append((left.upper, left.upper_inclusive))
    if right.upper is not None:
        candidates.append((right.upper, right.upper_inclusive))
    if not candidates:
        return None, False
    upper, inclusive = candidates[0]
    for value, candidate_inclusive in candidates[1:]:
        if value < upper:
            upper, inclusive = value, candidate_inclusive
        elif value == upper:
            inclusive = inclusive and candidate_inclusive
    return upper, inclusive


def _discrete_constraints_disjoint(
    left: _DiscreteConstraint,
    right: _DiscreteConstraint,
) -> bool:
    if left.equals is not None and right.equals is not None:
        return left.equals != right.equals
    if left.equals is not None:
        return left.equals in right.excluded
    if right.equals is not None:
        return right.equals in left.excluded
    return False


def _conditions_disjoint(left: _ConditionSummary, right: _ConditionSummary) -> bool:
    for name in set(left.numeric) & set(right.numeric):
        if _numeric_constraints_disjoint(left.numeric[name], right.numeric[name]):
            return True
    for name in set(left.discrete) & set(right.discrete):
        if _discrete_constraints_disjoint(left.discrete[name], right.discrete[name]):
            return True
    return False
