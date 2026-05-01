from __future__ import annotations

from propstore.conflict_detector.equations import detect_equation_conflicts
from propstore.conflict_detector.models import (
    ConflictClaim,
    ConflictClaimVariable,
    ConflictClass,
)


def _claim(claim_id: str, expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="equation",
        expression=expression,
        variables=(
            ConflictClaimVariable(concept_id="output", symbol="y", role="dependent"),
            ConflictClaimVariable(concept_id="factor_a", symbol="x", role="independent"),
            ConflictClaimVariable(concept_id="factor_b", symbol="z", role="independent"),
        ),
    )


def test_equation_conflict_detector_skips_equivalent_orientations() -> None:
    records = detect_equation_conflicts([
        _claim("left", "y = x + z"),
        _claim("right", "x + z = y"),
    ], {})

    assert records == []


def test_equation_conflict_detector_reports_proven_difference() -> None:
    records = detect_equation_conflicts([
        _claim("linear", "y = x + z"),
        _claim("scaled", "y = 2*x + z"),
    ], {})

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONFLICT


def test_equation_conflict_detector_reports_undecidable_domain_sensitive_pair() -> None:
    records = detect_equation_conflicts([
        _claim("log_sum", "y = log(x * z)"),
        _claim("sum_logs", "y = log(x) + log(z)"),
    ], {})

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.UNKNOWN
