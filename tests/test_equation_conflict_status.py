from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.conflict_detector.equations import detect_equation_conflicts
from propstore.conflict_detector.models import (
    ConflictClaim,
    ConflictClaimVariable,
    ConflictClass,
)


def test_equation_conflict_detector_skips_equivalent_orientations() -> None:
    records = detect_equation_conflicts(
        [
            _claim("left", "y = x + z"),
            _claim("right", "x + z = y"),
        ],
        {},
    )

    assert records == []


def test_equation_conflict_detector_reports_proven_difference() -> None:
    records = detect_equation_conflicts(
        [
            _claim("linear", "y = x + z"),
            _claim("scaled", "y = 2*x + z"),
        ],
        {},
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONFLICT


def test_equation_conflict_detector_reports_undecidable_domain_sensitive_pair() -> None:
    records = detect_equation_conflicts(
        [
            _claim("log_sum", "y = log(x * z)"),
            _claim("sum_logs", "y = log(x) + log(z)"),
        ],
        {},
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.UNKNOWN


@pytest.mark.property
@given(
    left_offset=st.integers(min_value=1, max_value=5),
    right_offset=st.integers(min_value=1, max_value=5),
)
@settings(deadline=None, max_examples=25)
def test_equation_conflict_detection_is_symmetric(
    left_offset: int,
    right_offset: int,
) -> None:
    claim_a = _claim("claim_a", f"y = x + {left_offset}")
    claim_b = _claim("claim_b", f"y = x + {right_offset}")

    records_ab = detect_equation_conflicts([claim_a, claim_b], {})
    records_ba = detect_equation_conflicts([claim_b, claim_a], {})

    assert len(records_ab) == len(records_ba)
    if records_ab:
        assert records_ab[0].warning_class == records_ba[0].warning_class
