from __future__ import annotations

from propstore.sympy_generator import (
    generate_sympy_equation,
    generate_sympy_rhs,
    generate_sympy_rhs_with_error,
)


def test_rhs_generator_name_declares_rhs_only_contract() -> None:
    result = generate_sympy_rhs_with_error("y = f(x)")

    assert result.expression == "f(x)"
    assert result.error is None
    assert generate_sympy_rhs("y = f(x)") == "f(x)"


def test_equation_generator_preserves_distinct_left_hand_sides() -> None:
    y_equation = generate_sympy_equation("y = f(x)")
    z_equation = generate_sympy_equation("z = f(x)")

    assert y_equation.error is None
    assert z_equation.error is None
    assert y_equation.lhs == "y"
    assert z_equation.lhs == "z"
    assert y_equation != z_equation
