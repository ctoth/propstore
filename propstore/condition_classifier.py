"""Condition classification for the propstore conflict detector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.cel_types import CelExpr
from propstore.core.conditions import checked_condition_set
from propstore.core.conditions.cel_frontend import check_condition_ir
from propstore.core.conditions.registry import ConceptInfo
from propstore.core.conditions.solver import SolverSat, SolverUnknown, SolverUnsat
from propstore.conflict_detector.models import ConflictClass

if TYPE_CHECKING:
    from propstore.core.conditions.solver import ConditionSolver


def _try_z3_classify(
    conditions_a: list[CelExpr],
    conditions_b: list[CelExpr],
    cel_registry: dict[str, ConceptInfo] | None,
    solver: ConditionSolver | None = None,
) -> ConflictClass:
    """Classify conditions using Z3, failing loudly if Z3 is unavailable."""
    if cel_registry is None:
        raise ValueError("classify_conditions requires a CEL registry for Z3 reasoning")

    if solver is None:
        from propstore.core.conditions.solver import ConditionSolver

        solver = ConditionSolver(cel_registry)

    checked_a = checked_condition_set(
        check_condition_ir(str(condition), cel_registry) for condition in conditions_a
    )
    checked_b = checked_condition_set(
        check_condition_ir(str(condition), cel_registry) for condition in conditions_b
    )

    equivalence = solver.are_equivalent_result(checked_a, checked_b)
    if isinstance(equivalence, SolverUnknown):
        return ConflictClass.UNKNOWN
    if isinstance(equivalence, SolverUnsat):
        return ConflictClass.CONFLICT
    if not isinstance(equivalence, SolverSat):
        raise TypeError(f"Unexpected solver result: {type(equivalence).__name__}")

    disjointness = solver.are_disjoint_result(checked_a, checked_b)
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
    solver: ConditionSolver | None = None,
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
