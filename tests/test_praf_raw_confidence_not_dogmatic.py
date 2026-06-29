"""A raw confidence number is not subjective-logic evidence.

CLAUDE.md honest ignorance: a stated confidence of 1.0 is not a dogmatic
certainty, and a bare confidence with no effective sample size carries no
evidence count. Both yield a typed :class:`NoCalibration`, never a fabricated
opinion.
"""

from __future__ import annotations

from propstore.praf import NoCalibration, p_relation_from_stance


def test_raw_confidence_one_is_not_dogmatic_evidence() -> None:
    result = p_relation_from_stance({"confidence": 1.0, "opinion_base_rate": 0.5})
    assert isinstance(result, NoCalibration)
    assert result.reason == "raw_confidence_not_evidence"
    assert "effective_sample_size" in result.missing_fields


def test_raw_confidence_half_without_sample_size_stays_uncalibrated() -> None:
    result = p_relation_from_stance({"confidence": 0.5, "opinion_base_rate": 0.5})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_evidence_count"
    assert "effective_sample_size" in result.missing_fields
