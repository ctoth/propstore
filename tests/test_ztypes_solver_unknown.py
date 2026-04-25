"""Regression tests for solver unknown propagation."""

from __future__ import annotations

from propstore.condition_classifier import _try_z3_classify
from propstore.conflict_detector.models import ConflictClass
from propstore.conflict_detector.parameter_claims import (
    _detect_cross_class_parameter_conflicts,
)
from propstore.merge.merge_classifier import _DiffKind
from propstore.z3_conditions import SolverUnknown, SolverUnknownReason


class UnknownEquivalenceSolver:
    def are_equivalent_result(self, conditions_a, conditions_b):
        return SolverUnknown(SolverUnknownReason.OTHER, "test unknown equivalence")

    def are_disjoint_result(self, conditions_a, conditions_b):
        raise AssertionError("disjointness must not be queried after UNKNOWN equivalence")


class UnknownDisjointSolver:
    def are_equivalent_result(self, conditions_a, conditions_b):
        from propstore.z3_conditions import SolverSat

        return SolverSat()

    def are_disjoint_result(self, conditions_a, conditions_b):
        return SolverUnknown(SolverUnknownReason.TIMEOUT, "test timeout")


def test_condition_classifier_returns_unknown_for_solver_unknown_equivalence():
    result = _try_z3_classify(
        ["x > 1"],
        ["x > 2"],
        {},
        solver=UnknownEquivalenceSolver(),
    )

    assert result == ConflictClass.UNKNOWN


def test_condition_classifier_returns_unknown_for_solver_unknown_disjointness():
    result = _try_z3_classify(
        ["x > 1"],
        ["x > 2"],
        {},
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
        lifting_system=None,
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.UNKNOWN


def test_repository_merge_unknown_is_ignorance_not_attack():
    assert _DiffKind.from_conflict_class(ConflictClass.UNKNOWN) == _DiffKind.UNKNOWN
