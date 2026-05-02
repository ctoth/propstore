"""Condition classification for the propstore conflict detector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.cel_types import CelExpr
from propstore.core.conditions.registry import ConceptInfo
from propstore.conflict_detector.models import ConflictClass
from propstore.z3_conditions import SolverSat, SolverUnknown, SolverUnsat

if TYPE_CHECKING:
    from propstore.z3_conditions import Z3ConditionSolver


def _try_z3_classify(
    conditions_a: list[CelExpr],
    conditions_b: list[CelExpr],
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

    equivalence = solver.are_equivalent_result(conditions_a, conditions_b)
    if isinstance(equivalence, SolverUnknown):
        return ConflictClass.UNKNOWN
    if isinstance(equivalence, SolverUnsat):
        return ConflictClass.CONFLICT
    if not isinstance(equivalence, SolverSat):
        raise TypeError(f"Unexpected solver result: {type(equivalence).__name__}")

    disjointness = solver.are_disjoint_result(conditions_a, conditions_b)
    if isinstance(disjointness, SolverUnknown):
        return ConflictClass.UNKNOWN
    if isinstance(disjointness, SolverUnsat):
        return ConflictClass.PHI_NODE
    if not isinstance(disjointness, SolverSat):
        raise TypeError(f"Unexpected solver result: {type(disjointness).__name__}")
    return ConflictClass.OVERLAP


def classify_conditions(
    conditions_a: list[CelExpr],
    conditions_b: list[CelExpr],
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
