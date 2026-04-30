from __future__ import annotations

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.equation_comparison import EquationComparisonStatus, compare_equation_claims


def _claim(claim_id: str, expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="equation",
        expression=expression,
        variables=(
            ConflictClaimVariable(concept_id="x", symbol="x", role="dependent"),
            ConflictClaimVariable(concept_id="y", symbol="y", role="independent"),
            ConflictClaimVariable(concept_id="z", symbol="z", role="independent"),
        ),
    )


def test_equation_comparison_is_orientation_invariant() -> None:
    comparison = compare_equation_claims(_claim("a", "x = y"), _claim("b", "y = x"))

    assert comparison.status == EquationComparisonStatus.EQUIVALENT


def test_equation_comparison_keeps_different_equations_distinct() -> None:
    comparison = compare_equation_claims(_claim("a", "x = y"), _claim("b", "x = z"))

    assert comparison.status == EquationComparisonStatus.DIFFERENT


def test_equation_comparison_normalizes_scaled_orientation() -> None:
    comparison = compare_equation_claims(
        _claim("a", "x = y"),
        _claim("b", "2 * y = 2 * x"),
    )

    assert comparison.status == EquationComparisonStatus.EQUIVALENT
