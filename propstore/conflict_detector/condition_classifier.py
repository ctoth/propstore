"""Condition classification for the conflict detector.

Decides how two differing-value claims relate by reasoning over their authored
CEL conditions with condition-ir's ``ConditionSolver`` — never an in-tree solver.
The dispatch is deliberately non-committal: any solver ``UNKNOWN`` yields
:attr:`ConflictClass.UNKNOWN` (honest ignorance), never a fabricated verdict.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from condition_ir import (
    CelExpr,
    ConceptInfo,
    ConditionSolver,
    SolverUnknown,
    SolverUnsat,
    check_condition_ir,
    checked_condition_set,
)

from .models import ConflictClass


def classify_conditions(
    conditions_a: Sequence[CelExpr],
    conditions_b: Sequence[CelExpr],
    cel_registry: Mapping[str, ConceptInfo] | None = None,
    *,
    solver: ConditionSolver | None = None,
) -> ConflictClass:
    """Classify a pair of differing-value claims by their conditions.

    Identical condition sets are an outright ``CONFLICT`` (same assumptions,
    different value). Otherwise the Z3-backed solver decides equivalence then
    disjointness.
    """

    if sorted(conditions_a) == sorted(conditions_b):
        return ConflictClass.CONFLICT
    return _z3_classify(conditions_a, conditions_b, cel_registry, solver=solver)


def _z3_classify(
    conditions_a: Sequence[CelExpr],
    conditions_b: Sequence[CelExpr],
    cel_registry: Mapping[str, ConceptInfo] | None,
    *,
    solver: ConditionSolver | None,
) -> ConflictClass:
    if cel_registry is None:
        raise ValueError("classify_conditions requires a CEL registry for Z3 reasoning")
    if solver is None:
        solver = ConditionSolver(cel_registry)

    checked_a = checked_condition_set(
        check_condition_ir(str(condition), cel_registry) for condition in conditions_a
    )
    checked_b = checked_condition_set(
        check_condition_ir(str(condition), cel_registry) for condition in conditions_b
    )

    # are_equivalent_result returns UNSAT when the two condition sets are
    # logically equivalent (their symmetric difference is unsatisfiable).
    equivalence = solver.are_equivalent_result(checked_a, checked_b)
    if isinstance(equivalence, SolverUnknown):
        return ConflictClass.UNKNOWN
    if isinstance(equivalence, SolverUnsat):
        return ConflictClass.CONFLICT

    # Equivalence is SAT (the sets are not equivalent): disjoint conditions are a
    # φ-node (both readings survive), overlapping ones are an OVERLAP.
    disjointness = solver.are_disjoint_result(checked_a, checked_b)
    if isinstance(disjointness, SolverUnknown):
        return ConflictClass.UNKNOWN
    if isinstance(disjointness, SolverUnsat):
        return ConflictClass.PHI_NODE
    return ConflictClass.OVERLAP
