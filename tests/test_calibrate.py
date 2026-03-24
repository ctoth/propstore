"""Tests for propstore.calibrate — calibration module."""

import math

import pytest

from propstore.calibrate import (
    CorpusCalibrator,
    TemperatureScaler,
    calibrated_probability_to_opinion,
    categorical_to_opinion,
    expected_calibration_error,
)
from propstore.opinion import Opinion


# ---------------------------------------------------------------------------
# Temperature Scaling
# ---------------------------------------------------------------------------


def test_temperature_scaling_preserves_argmax():
    """Guo 2017, p.5: temperature scaling does not change argmax."""
    logits = [2.0, 5.0, 1.0, 3.0]
    raw_argmax = logits.index(max(logits))

    for t in [0.1, 0.5, 1.0, 2.0, 10.0]:
        scaler = TemperatureScaler(temperature=t)
        probs = scaler.calibrate_logits(logits)
        cal_argmax = probs.index(max(probs))
        assert cal_argmax == raw_argmax, f"argmax changed at T={t}"


def test_temperature_gt1_increases_entropy():
    """T > 1 softens the distribution, increasing entropy."""
    logits = [2.0, 5.0, 1.0]
    identity = TemperatureScaler(1.0).calibrate_logits(logits)
    soft = TemperatureScaler(3.0).calibrate_logits(logits)

    h_identity = -sum(p * math.log(p) for p in identity if p > 0)
    h_soft = -sum(p * math.log(p) for p in soft if p > 0)
    assert h_soft > h_identity


def test_temperature_lt1_decreases_entropy():
    """T < 1 sharpens the distribution, decreasing entropy."""
    logits = [2.0, 5.0, 1.0]
    identity = TemperatureScaler(1.0).calibrate_logits(logits)
    sharp = TemperatureScaler(0.5).calibrate_logits(logits)

    h_identity = -sum(p * math.log(p) for p in identity if p > 0)
    h_sharp = -sum(p * math.log(p) for p in sharp if p > 0)
    assert h_sharp < h_identity


def test_temperature_1_is_identity():
    """T = 1 produces standard softmax."""
    logits = [1.0, 2.0, 3.0]
    scaler = TemperatureScaler(1.0)
    probs = scaler.calibrate_logits(logits)

    # Manual softmax
    max_z = max(logits)
    exps = [math.exp(z - max_z) for z in logits]
    total = sum(exps)
    expected = [e / total for e in exps]

    for p, e in zip(probs, expected):
        assert abs(p - e) < 1e-10


def test_temperature_invalid():
    """T <= 0 should raise."""
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=0.0)
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=-1.0)


def test_temperature_fit():
    """fit() should find a reasonable temperature on synthetic data."""
    # Overconfident logits: large magnitudes but label is class 0
    logits_list = [[5.0, 1.0, 1.0]] * 20 + [[1.0, 5.0, 1.0]] * 10
    labels = [0] * 20 + [1] * 10
    scaler = TemperatureScaler.fit(logits_list, labels)
    assert scaler.temperature > 0


# ---------------------------------------------------------------------------
# Corpus Calibrator
# ---------------------------------------------------------------------------


def test_corpus_calibrator_percentile_bounds():
    """Percentile must be in [0, 1]."""
    cal = CorpusCalibrator([0.1, 0.3, 0.5, 0.7, 0.9])
    # Below min
    assert 0.0 <= cal.percentile(0.0) <= 1.0
    # Above max
    assert 0.0 <= cal.percentile(10.0) <= 1.0
    # In range
    assert 0.0 <= cal.percentile(0.5) <= 1.0


def test_corpus_calibrator_monotonicity():
    """Smaller distance -> smaller percentile (more similar)."""
    cal = CorpusCalibrator([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    p1 = cal.percentile(0.2)
    p2 = cal.percentile(0.8)
    assert p1 <= p2


def test_corpus_calibrator_uncertainty_scales_with_n():
    """Opinion uncertainty should scale approximately as 1/sqrt(n).

    More reference points -> narrower (less uncertain) opinion.
    """
    small_ref = [float(i) / 10 for i in range(10)]
    large_ref = [float(i) / 1000 for i in range(1000)]

    cal_small = CorpusCalibrator(small_ref)
    cal_large = CorpusCalibrator(large_ref)

    op_small = cal_small.to_opinion(0.05)
    op_large = cal_large.to_opinion(0.05)

    # Larger corpus should give less uncertainty
    assert op_large.u < op_small.u


# ---------------------------------------------------------------------------
# Categorical to Opinion
# ---------------------------------------------------------------------------


def test_categorical_without_calibration_returns_vacuous():
    """Without calibration data, opinion should be vacuous (u ~ 1.0)."""
    op = categorical_to_opinion("strong", 1)
    assert abs(op.u - 1.0) < 1e-9
    assert abs(op.b) < 1e-9
    assert abs(op.d) < 1e-9


def test_categorical_with_calibration_returns_informative():
    """With calibration counts, opinion should be informative (u < 1.0)."""
    counts = {
        (1, "strong"): (80, 100),
        (1, "moderate"): (60, 100),
    }
    op = categorical_to_opinion("strong", 1, calibration_counts=counts)
    assert op.u < 1.0
    # Expectation should be near the empirical accuracy (80/100 = 0.8)
    assert abs(op.expectation() - 0.8) < 0.1


def test_categorical_unknown_category():
    """Unknown category should raise."""
    with pytest.raises(ValueError, match="Unknown category"):
        categorical_to_opinion("fantastic", 1)


# ---------------------------------------------------------------------------
# Calibrated Probability to Opinion
# ---------------------------------------------------------------------------


def test_calibrated_prob_n0_returns_vacuous():
    """n=0 should return vacuous opinion."""
    op = calibrated_probability_to_opinion(0.8, 0.0)
    assert abs(op.u - 1.0) < 1e-9


def test_calibrated_prob_large_n_returns_narrow():
    """Large n should give narrow opinion near the probability."""
    op = calibrated_probability_to_opinion(0.8, 1000.0)
    assert op.u < 0.01
    assert abs(op.expectation() - 0.8) < 0.01


# ---------------------------------------------------------------------------
# ECE
# ---------------------------------------------------------------------------


def test_ece_perfect_calibration():
    """ECE = 0 for perfectly calibrated predictions."""
    # All predictions at 1.0 confidence and all correct
    confidences = [1.0] * 50
    correct = [True] * 50
    ece = expected_calibration_error(confidences, correct)
    assert abs(ece) < 1e-9


def test_ece_miscalibrated():
    """ECE > 0 for miscalibrated predictions."""
    # High confidence but half wrong
    confidences = [0.9] * 100
    correct = [True] * 50 + [False] * 50
    ece = expected_calibration_error(confidences, correct)
    assert ece > 0.3  # Should be ~0.4


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_roundtrip_categorical_to_expectation():
    """categorical -> opinion -> expectation recovers calibrated probability."""
    counts = {(1, "strong"): (85, 100)}
    op = categorical_to_opinion("strong", 1, calibration_counts=counts)
    # r=85, s=15 -> b=85/102, d=15/102, u=2/102
    # expectation = b + a*u = 85/102 + 0.7 * 2/102
    # The empirical prob is 85/100 = 0.85
    # With W=2 prior, expectation ≈ (85 + 0.7*2) / 102 ≈ 0.847
    expected_emp = (85 + 0.7 * 2) / 102
    assert abs(op.expectation() - expected_emp) < 1e-6
