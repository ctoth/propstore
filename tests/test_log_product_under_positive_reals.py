from __future__ import annotations

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.equation_comparison import (
    EquationComparisonStatus,
    Positive,
    compare_equation_claims,
)


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


def test_log_product_equivalence_under_positive_reals() -> None:
    comparison = compare_equation_claims(
        _claim("a", "log(x * y) = z"),
        _claim("b", "log(x) + log(y) = z"),
        domain_assumptions=(Positive("x"), Positive("y")),
    )

    assert comparison.status == EquationComparisonStatus.EQUIVALENT


def test_log_product_without_positive_reals_is_unknown() -> None:
    comparison = compare_equation_claims(
        _claim("a", "log(x * y) = z"),
        _claim("b", "log(x) + log(y) = z"),
    )

    assert comparison.status == EquationComparisonStatus.UNKNOWN


def test_wrong_log_product_identity_under_positive_reals_is_different() -> None:
    comparison = compare_equation_claims(
        _claim("a", "log(x * y) = z"),
        _claim("b", "log(x) - log(y) = z"),
        domain_assumptions=(Positive("x"), Positive("y")),
    )

    assert comparison.status == EquationComparisonStatus.DIFFERENT
