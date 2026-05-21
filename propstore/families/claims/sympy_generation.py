"""Equation sympy derivation for claim semantic checks and storage rows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquationSympyDerivation:
    generated: str | None
    error: str | None


def derive_equation_sympy(
    *,
    authored_sympy: str | None,
    expression: str | None,
) -> EquationSympyDerivation:
    from human_to_sympy import generate_sympy_rhs_with_error

    if authored_sympy:
        sympy_result = generate_sympy_rhs_with_error(authored_sympy)
        return EquationSympyDerivation(
            generated=authored_sympy if sympy_result.expression is not None else None,
            error=sympy_result.error if sympy_result.expression is None else None,
        )
    if expression:
        generated = generate_sympy_rhs_with_error(expression)
        return EquationSympyDerivation(
            generated=generated.expression,
            error=generated.error if generated.expression is None else None,
        )
    return EquationSympyDerivation(generated=None, error=None)
