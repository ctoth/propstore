from __future__ import annotations

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.equation_comparison import (
    EquationComparisonStatus,
    Real,
    compare_equation_claims,
)


def _claim(claim_id: str, expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="equation",
        expression=expression,
        variables=(
            ConflictClaimVariable(concept_id="a", symbol="a", role="independent"),
            ConflictClaimVariable(concept_id="b", symbol="b", role="independent"),
            ConflictClaimVariable(concept_id="z", symbol="z", role="dependent"),
        ),
    )


def test_exp_sum_product_equivalence_under_reals() -> None:
    comparison = compare_equation_claims(
        _claim("a", "exp(a + b) = z"),
        _claim("b", "exp(a) * exp(b) = z"),
        domain_assumptions=(Real("a"), Real("b")),
    )

    assert comparison.status == EquationComparisonStatus.EQUIVALENT


def test_exp_sum_product_without_declared_domain_is_unknown() -> None:
    comparison = compare_equation_claims(
        _claim("a", "exp(a + b) = z"),
        _claim("b", "exp(a) * exp(b) = z"),
    )

    assert comparison.status == EquationComparisonStatus.UNKNOWN
