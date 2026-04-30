from __future__ import annotations

from propstore.cel_checker import ConceptInfo, KindType
from propstore.z3_conditions import Z3ConditionSolver


def _solver() -> Z3ConditionSolver:
    return Z3ConditionSolver(
        {
            "enabled": ConceptInfo("enabled-id", "enabled", KindType.BOOLEAN),
            "x": ConceptInfo("x-id", "x", KindType.QUANTITY),
        }
    )


def test_or_short_circuits_undefined_division_when_left_disjunct_true() -> None:
    assert _solver().is_condition_satisfied(
        "enabled || (1 / x > 0)",
        {"enabled": True, "x": 0.0},
    )


def test_or_short_circuits_undefined_division_when_right_disjunct_true() -> None:
    assert _solver().is_condition_satisfied(
        "(1 / x > 0) || true",
        {"enabled": False, "x": 0.0},
    )


def test_ternary_ignores_undefined_unselected_branch() -> None:
    assert _solver().is_condition_satisfied(
        "enabled ? true : (1 / x > 0)",
        {"enabled": True, "x": 0.0},
    )


def test_bare_division_condition_is_not_satisfied_when_denominator_is_zero() -> None:
    assert not _solver().is_condition_satisfied(
        "1 / x > 0",
        {"enabled": True, "x": 0.0},
    )
