"""Condition classification for the propstore conflict detector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.cel_checker import ConceptInfo
from propstore.conflict_detector.models import ConflictClass

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver


def _try_z3_classify(
    conditions_a: list[str],
    conditions_b: list[str],
    cel_registry: dict[str, ConceptInfo] | None,
    solver: Z3ConditionSolver | None = None,
) -> ConflictClass:
    """Classify conditions using Z3, failing loudly if Z3 is unavailable."""
    if cel_registry is None:
        raise ValueError("classify_conditions requires a CEL registry for Z3 reasoning")

    if solver is None:
        try:
            from propstore.z3_conditions import Z3ConditionSolver
        except ImportError as exc:
            raise RuntimeError("Z3 condition reasoning is required but unavailable") from exc
        solver = Z3ConditionSolver(cel_registry)

    if solver.are_equivalent(conditions_a, conditions_b):
        return ConflictClass.CONFLICT
    if solver.are_disjoint(conditions_a, conditions_b):
        return ConflictClass.PHI_NODE
    return ConflictClass.OVERLAP


def classify_conditions(
    conditions_a: list[str],
    conditions_b: list[str],
    cel_registry: dict[str, ConceptInfo] | None = None,
    *,
    solver: Z3ConditionSolver | None = None,
) -> ConflictClass:
    """Classify a pair of differing-value claims based on their conditions."""
    normalized_a = sorted(conditions_a)
    normalized_b = sorted(conditions_b)
    if normalized_a == normalized_b:
        return ConflictClass.CONFLICT
    return _try_z3_classify(
        conditions_a,
        conditions_b,
        cel_registry,
        solver=solver,
    )
