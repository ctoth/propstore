"""PrAF stance confidence must not fabricate one-sample evidence."""

import pytest

from propstore.opinion import Opinion
from propstore.praf import NoCalibration, p_relation_from_stance
from propstore.provenance import ProvenanceStatus


def test_p_relation_from_stance_confidence_without_sample_size_is_uncalibrated() -> None:
    opinion = p_relation_from_stance(
        {
            "confidence": 0.5,
            "opinion_base_rate": 0.5,
        }
    )

    assert isinstance(opinion, NoCalibration)
    assert opinion.reason == "missing_evidence_count"
    assert opinion.missing_fields == ("effective_sample_size", "sample_size")
    assert opinion.provenance is not None
    assert "missing_evidence_count" in opinion.provenance.operations


def test_p_relation_from_stance_uses_effective_sample_size_when_present() -> None:
    opinion = p_relation_from_stance(
        {
            "confidence": 0.75,
            "effective_sample_size": 10,
            "opinion_base_rate": 0.5,
        }
    )

    assert isinstance(opinion, Opinion)
    assert opinion.u < 1.0
    assert opinion.expectation() == pytest.approx(0.75, abs=0.05)
    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.STATED
    assert "stance_confidence" in opinion.provenance.operations
