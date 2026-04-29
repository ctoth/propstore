from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.praf.engine import _defeat_summary_opinion
from propstore.provenance import ProvenanceStatus


@pytest.mark.property
@given(probability=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(deadline=None, max_examples=50)
def test_defeat_summary_probability_never_claims_calibrated_evidence(probability):
    """Cluster F #3/#14: scalar defeat marginals cannot manufacture evidence."""
    opinion = _defeat_summary_opinion(probability)

    assert 0.0 <= opinion.b <= 1.0
    assert 0.0 <= opinion.d <= 1.0
    assert 0.0 <= opinion.u <= 1.0
    assert opinion.b + opinion.d + opinion.u == pytest.approx(1.0)
    assert opinion.u == pytest.approx(1.0)
    assert opinion.a == pytest.approx(probability, abs=1e-9)
    assert opinion.provenance is not None
    assert opinion.provenance.status is not ProvenanceStatus.CALIBRATED
