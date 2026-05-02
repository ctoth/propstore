"""Regression tests for solver unknown propagation."""

from __future__ import annotations

from propstore.condition_classifier import _try_z3_classify
from propstore.conflict_detector.models import ConflictClass
from propstore.conflict_detector.parameter_claims import (
    _detect_cross_class_parameter_conflicts,
)
from propstore.core.conditions import checked_condition_set
from propstore.core.conditions.cel_frontend import check_condition_ir
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.merge.merge_classifier import _DiffKind
from propstore.core.conditions.solver import (
    SolverSat,
    SolverUnknown,
    SolverUnknownReason,
)


def _registry():
    return {
        "x": ConceptInfo(id="x", canonical_name="x", kind=KindType.QUANTITY),
    }


def _condition_set(*sources: str):
    registry = _registry()
    return checked_condition_set(check_condition_ir(source, registry) for source in sources)


class UnknownEquivalenceSolver:
    def are_equivalent_result(self, conditions_a, conditions_b):
        return SolverUnknown(SolverUnknownReason.OTHER, "test unknown equivalence")

    def are_disjoint_result(self, conditions_a, conditions_b):
        raise AssertionError("disjointness must not be queried after UNKNOWN equivalence")


class UnknownDisjointSolver:
    def are_equivalent_result(self, conditions_a, conditions_b):
        return SolverSat()

    def are_disjoint_result(self, conditions_a, conditions_b):
        return SolverUnknown(SolverUnknownReason.TIMEOUT, "test timeout")


def test_condition_classifier_returns_unknown_for_solver_unknown_equivalence():
    result = _try_z3_classify(
        ["x > 1"],
        ["x > 2"],
        _registry(),
        solver=UnknownEquivalenceSolver(),
    )

    assert result == ConflictClass.UNKNOWN


def test_condition_classifier_returns_unknown_for_solver_unknown_disjointness():
    result = _try_z3_classify(
        ["x > 1"],
        ["x > 2"],
        _registry(),
        solver=UnknownDisjointSolver(),
    )

    assert result == ConflictClass.UNKNOWN


def test_parameter_cross_class_conflict_preserves_unknown_warning_class():
    from propstore.conflict_detector.models import ConflictClaim

    records = []
    claims = [
        ConflictClaim(claim_id="a", output_concept_id="freq", value=1),
        ConflictClaim(claim_id="b", output_concept_id="freq", value=2),
    ]

    _detect_cross_class_parameter_conflicts(
        records,
        "freq",
        claims,
        [["x > 1"], ["x > 2"]],
        [[0], [1]],
        {},
        UnknownDisjointSolver(),
        [_condition_set("x > 1"), _condition_set("x > 2")],
        lifting_system=None,
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.UNKNOWN


def test_repository_merge_unknown_is_ignorance_not_attack():
    assert _DiffKind.from_conflict_class(ConflictClass.UNKNOWN) == _DiffKind.UNKNOWN
