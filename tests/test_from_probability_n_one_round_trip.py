"""PrAF stance confidence must not fabricate one-sample evidence."""

import pytest

from propstore.opinion import Opinion
from propstore.praf import p_relation_from_stance
from propstore.provenance import ProvenanceStatus


def test_p_relation_from_stance_confidence_without_sample_size_is_vacuous() -> None:
    opinion = p_relation_from_stance(
        {
            "confidence": 0.5,
            "opinion_base_rate": 0.5,
        }
    )

    assert isinstance(opinion, Opinion)
    assert opinion.b == pytest.approx(0.0)
    assert opinion.d == pytest.approx(0.0)
    assert opinion.u == pytest.approx(1.0)
    assert opinion.a == pytest.approx(0.5)
    assert opinion.expectation() == pytest.approx(0.5)
    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.VACUOUS
    assert "stance_confidence_without_sample_size" in opinion.provenance.operations


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
