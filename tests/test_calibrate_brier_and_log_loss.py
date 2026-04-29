from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def test_brier_score_matches_guo_2017_mean_squared_confidence_error():
    """Cluster F #25: Guo 2017 reports Brier alongside calibration error."""
    from propstore.calibrate import brier_score

    assert brier_score([0.0, 1.0, 0.8], [False, True, True]) == pytest.approx(
        (0.0 + 0.0 + 0.04) / 3.0
    )


def test_log_loss_matches_guo_2017_negative_log_likelihood():
    """Cluster F #25: log-loss/NLL must be a public calibration metric."""
    from propstore.calibrate import log_loss

    expected = -(math.log(0.9) + math.log(0.8) + math.log(1.0 - 0.2)) / 3.0
    assert log_loss([0.9, 0.8, 0.2], [True, True, False]) == pytest.approx(expected)


@pytest.mark.property
@given(confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(deadline=None, max_examples=40)
def test_brier_score_is_bounded_for_single_binary_event(confidence):
    from propstore.calibrate import brier_score

    assert 0.0 <= brier_score([confidence], [True]) <= 1.0
    assert 0.0 <= brier_score([confidence], [False]) <= 1.0
