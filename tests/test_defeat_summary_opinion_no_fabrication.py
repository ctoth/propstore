"""PrAF defeat-summary opinions must not fabricate calibration."""

import pytest

from propstore.praf.engine import _defeat_summary_opinion
from propstore.provenance import ProvenanceStatus


def test_defeat_summary_uses_vacuous_for_uncalibrated_probability() -> None:
    opinion = _defeat_summary_opinion(0.25)

    assert opinion.b == pytest.approx(0.0)
    assert opinion.d == pytest.approx(0.0)
    assert opinion.u == pytest.approx(1.0)
    assert opinion.a == pytest.approx(0.25)
    assert opinion.expectation() == pytest.approx(0.25)
    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.VACUOUS
    assert "defeat_probability_uncalibrated" in opinion.provenance.operations


@pytest.mark.parametrize("probability", [1e-9, 0.999999, 0.0, 1.0])
def test_defeat_summary_no_crash_at_probability_boundary(probability: float) -> None:
    opinion = _defeat_summary_opinion(probability)

    assert opinion.b == pytest.approx(0.0)
    assert opinion.d == pytest.approx(0.0)
    assert opinion.u == pytest.approx(1.0)
    assert opinion.provenance is not None
    assert opinion.provenance.status is ProvenanceStatus.VACUOUS
