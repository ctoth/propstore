"""Defeat-summary marginals are reported honestly, never as fabricated evidence.

An exact defeat marginal is a *probability*, not calibrated belief. The summary
opinion is therefore vacuous (``u = 1``) with the marginal as its base rate and
``VACUOUS`` provenance — the system never claims belief/disbelief evidence it does
not have (CLAUDE.md honest ignorance; Jøsang 2001, p.8).
"""

from __future__ import annotations

import pytest

from propstore.opinion_provenance import OpinionWithProvenance
from propstore.praf.engine import _defeat_summary_opinion
from propstore.provenance import ProvenanceStatus


@pytest.mark.parametrize("probability", [0.0, 0.25, 0.5, 0.75, 1.0, 1e-9, 0.999999])
def test_defeat_summary_never_claims_calibrated_evidence(probability: float) -> None:
    result = _defeat_summary_opinion(probability)
    assert isinstance(result, OpinionWithProvenance)
    opinion = result.opinion
    assert 0.0 <= opinion.b <= 1.0
    assert 0.0 <= opinion.d <= 1.0
    assert 0.0 <= opinion.u <= 1.0
    assert opinion.b + opinion.d + opinion.u == pytest.approx(1.0)
    assert opinion.u == pytest.approx(1.0)
    assert result.provenance.status is not ProvenanceStatus.CALIBRATED


def test_defeat_summary_uses_vacuous_for_uncalibrated_probability() -> None:
    result = _defeat_summary_opinion(0.25)
    assert result.opinion.b == pytest.approx(0.0)
    assert result.opinion.d == pytest.approx(0.0)
    assert result.opinion.u == pytest.approx(1.0)
    assert result.opinion.base_rate == pytest.approx(0.25)
    assert result.opinion.expectation() == pytest.approx(0.25)
    assert result.provenance.status is ProvenanceStatus.VACUOUS
    assert "defeat_probability_uncalibrated" in result.provenance.operations


@pytest.mark.parametrize("boundary", [1e-9, 0.999999, 0.0, 1.0])
def test_defeat_summary_no_crash_at_probability_boundary(boundary: float) -> None:
    result = _defeat_summary_opinion(boundary)
    assert result.opinion.b == pytest.approx(0.0)
    assert result.opinion.d == pytest.approx(0.0)
    assert result.opinion.u == pytest.approx(1.0)
    assert result.provenance.status is ProvenanceStatus.VACUOUS
