from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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


@pytest.mark.property
@given(numerator=st.integers(min_value=1, max_value=25))
@settings(deadline=None, max_examples=25)
def test_generated_or_short_circuits_division_definedness(numerator: int) -> None:
    solver = _solver()

    assert solver.is_condition_satisfied(
        f"enabled || ({numerator} / x > 0)",
        {"enabled": True, "x": 0.0},
    )
    assert not solver.is_condition_satisfied(
        f"false || ({numerator} / x > 0)",
        {"enabled": False, "x": 0.0},
    )


@pytest.mark.property
@given(numerator=st.integers(min_value=1, max_value=25), choice=st.booleans())
@settings(deadline=None, max_examples=25)
def test_generated_ternary_short_circuits_division_definedness(
    numerator: int,
    choice: bool,
) -> None:
    solver = _solver()
    expression = (
        f"enabled ? true : ({numerator} / x > 0)"
        if choice
        else f"enabled ? ({numerator} / x > 0) : true"
    )

    assert solver.is_condition_satisfied(
        expression,
        {"enabled": choice, "x": 0.0},
    )
