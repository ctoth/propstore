from __future__ import annotations

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.equation_comparison import (
    EquationComparisonStatus,
    NonNegative,
    Real,
    compare_equation_claims,
)


def _claim(claim_id: str, expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="equation",
        expression=expression,
        variables=(
            ConflictClaimVariable(concept_id="x", symbol="x", role="dependent"),
            ConflictClaimVariable(concept_id="z", symbol="z", role="independent"),
        ),
    )


def test_sqrt_square_equivalence_under_nonnegative_reals() -> None:
    comparison = compare_equation_claims(
        _claim("a", "sqrt(x * x) = z"),
        _claim("b", "x = z"),
        domain_assumptions=(NonNegative("x"),),
    )

    assert comparison.status == EquationComparisonStatus.EQUIVALENT


def test_sqrt_square_without_nonnegative_domain_is_unknown() -> None:
    comparison = compare_equation_claims(
        _claim("a", "sqrt(x * x) = z"),
        _claim("b", "x = z"),
    )

    assert comparison.status == EquationComparisonStatus.UNKNOWN


def test_sqrt_square_abs_equivalence_under_reals() -> None:
    comparison = compare_equation_claims(
        _claim("a", "sqrt(x * x) = z"),
        _claim("b", "abs(x) = z"),
        domain_assumptions=(Real("x"),),
    )

    assert comparison.status == EquationComparisonStatus.EQUIVALENT


def test_sqrt_square_abs_without_real_domain_is_unknown() -> None:
    comparison = compare_equation_claims(
        _claim("a", "sqrt(x * x) = z"),
        _claim("b", "abs(x) = z"),
    )

    assert comparison.status == EquationComparisonStatus.UNKNOWN
