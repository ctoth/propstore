"""Tests for propstore.heuristic.calibrate — calibration to the opinion algebra.

Covers the pure numeric surface (temperature scaling, corpus CDF calibration,
categorical mapping, calibrated-probability mapping, ECE). The sidecar-backed
calibration-counts projection and the schema CHECK constraints depend on the
world/build sidecar infrastructure and land in a later phase.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from doxa import Opinion

from propstore.core.base_rates import BaseRateUnresolved
from propstore.heuristic.calibrate import (
    CalibrationSource,
    CategoryPrior,
    CorpusCalibrator,
    TemperatureScaler,
    calibrated_probability_to_opinion,
    categorical_to_opinion,
    expected_calibration_error,
)
from propstore.provenance import Provenance, ProvenanceStatus


def _category_prior(category: str, value: float = 0.5) -> CategoryPrior:
    return CategoryPrior(
        category=category,
        value=value,
        source=CalibrationSource.MEASURED,
        provenance=Provenance(
            status=ProvenanceStatus.CALIBRATED,
            witnesses=(),
            operations=("test_category_prior",),
        ),
    )


# --- Temperature scaling (Guo 2017) ---


def test_temperature_scaling_preserves_argmax() -> None:
    logits = [2.0, 5.0, 1.0, 3.0]
    raw_argmax = logits.index(max(logits))
    for t in [0.1, 0.5, 1.0, 2.0, 10.0]:
        probs = TemperatureScaler(temperature=t).calibrate_logits(logits)
        assert probs.index(max(probs)) == raw_argmax


def test_temperature_gt1_increases_entropy() -> None:
    logits = [2.0, 5.0, 1.0]
    identity = TemperatureScaler(1.0).calibrate_logits(logits)
    soft = TemperatureScaler(3.0).calibrate_logits(logits)
    h_identity = -sum(p * math.log(p) for p in identity if p > 0)
    h_soft = -sum(p * math.log(p) for p in soft if p > 0)
    assert h_soft > h_identity


def test_temperature_lt1_decreases_entropy() -> None:
    logits = [2.0, 5.0, 1.0]
    identity = TemperatureScaler(1.0).calibrate_logits(logits)
    sharp = TemperatureScaler(0.5).calibrate_logits(logits)
    h_identity = -sum(p * math.log(p) for p in identity if p > 0)
    h_sharp = -sum(p * math.log(p) for p in sharp if p > 0)
    assert h_sharp < h_identity


def test_temperature_1_is_identity() -> None:
    logits = [1.0, 2.0, 3.0]
    probs = TemperatureScaler(1.0).calibrate_logits(logits)
    max_z = max(logits)
    exps = [math.exp(z - max_z) for z in logits]
    total = sum(exps)
    expected = [e / total for e in exps]
    for p, e in zip(probs, expected):
        assert abs(p - e) < 1e-10


def test_temperature_invalid() -> None:
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=0.0)
    with pytest.raises(ValueError):
        TemperatureScaler(temperature=-1.0)


def test_temperature_fit() -> None:
    logits_list = [[5.0, 1.0, 1.0]] * 20 + [[1.0, 5.0, 1.0]] * 10
    labels = [0] * 20 + [1] * 10
    scaler = TemperatureScaler.fit(logits_list, labels)
    assert scaler.temperature > 0


# --- Corpus calibrator ---


def test_corpus_calibrator_percentile_bounds() -> None:
    cal = CorpusCalibrator([0.1, 0.3, 0.5, 0.7, 0.9], corpus_base_rate=0.5)
    assert 0.0 <= cal.percentile(0.0) <= 1.0
    assert 0.0 <= cal.percentile(10.0) <= 1.0
    assert 0.0 <= cal.percentile(0.5) <= 1.0


def test_corpus_calibrator_monotonicity() -> None:
    cal = CorpusCalibrator(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        corpus_base_rate=0.5,
    )
    assert cal.percentile(0.2) <= cal.percentile(0.8)


def test_corpus_calibrator_requires_explicit_base_rate() -> None:
    with pytest.raises(TypeError):
        CorpusCalibrator([0.1, 0.2, 0.3])


def test_corpus_calibrator_from_cdf_requires_explicit_base_rate() -> None:
    with pytest.raises(TypeError):
        CorpusCalibrator.from_cdf([0.1, 0.2, 0.3])


def test_corpus_calibrator_uncertainty_scales_with_n() -> None:
    small_ref = [float(i) / 10 for i in range(10)]
    large_ref = [float(i) / 1000 for i in range(1000)]
    op_small = CorpusCalibrator(small_ref, corpus_base_rate=0.5).to_opinion(0.05)
    op_large = CorpusCalibrator(large_ref, corpus_base_rate=0.5).to_opinion(0.05)
    assert op_large.u < op_small.u


def test_large_corpus_does_not_produce_near_dogmatic_opinion() -> None:
    ref = [i / 10_000 for i in range(10_000)]
    cal = CorpusCalibrator(ref, corpus_base_rate=0.5)
    assert cal.to_opinion(0.5).u > 0.01


def test_single_element_corpus_produces_near_vacuous_opinion() -> None:
    cal = CorpusCalibrator([0.5], corpus_base_rate=0.5)
    assert cal.to_opinion(0.3).u > 0.9


@pytest.mark.property
@given(
    ref_distances=st.lists(
        st.floats(min_value=0.0, max_value=2.0), min_size=1, max_size=100
    ),
    query_distance=st.floats(min_value=0.0, max_value=2.0),
)
@settings(deadline=None)
def test_corpus_opinion_bdu_sum_is_one(ref_distances, query_distance) -> None:
    op = CorpusCalibrator(ref_distances, corpus_base_rate=0.5).to_opinion(query_distance)
    assert abs((op.b + op.d + op.u) - 1.0) < 1e-9


# --- Categorical to opinion (honest ignorance) ---


def test_categorical_without_prior_returns_unresolved() -> None:
    result = categorical_to_opinion("strong", 1)
    assert isinstance(result, BaseRateUnresolved)
    assert result.reason == "missing_base_rate"


def test_categorical_with_calibration_returns_informative() -> None:
    counts = {(1, "strong"): (80, 100), (1, "moderate"): (60, 100)}
    op = categorical_to_opinion(
        "strong", 1, calibration_counts=counts, prior=_category_prior("strong")
    )
    assert isinstance(op, Opinion)
    assert op.u < 1.0
    assert abs(op.expectation() - 0.8) < 0.1


def test_categorical_without_counts_is_vacuous() -> None:
    op = categorical_to_opinion("strong", 1, prior=_category_prior("strong"))
    assert isinstance(op, Opinion)
    assert abs(op.u - 1.0) < 1e-9


def test_categorical_unknown_category() -> None:
    with pytest.raises(ValueError, match="Unknown category"):
        categorical_to_opinion("fantastic", 1)


def test_roundtrip_categorical_to_expectation() -> None:
    counts = {(1, "strong"): (85, 100)}
    op = categorical_to_opinion(
        "strong", 1, calibration_counts=counts, prior=_category_prior("strong")
    )
    assert isinstance(op, Opinion)
    expected_emp = (85 + 0.5 * 2) / 102
    assert abs(op.expectation() - expected_emp) < 1e-6


# --- Calibrated probability to opinion ---


def test_calibrated_prob_n0_returns_vacuous() -> None:
    op = calibrated_probability_to_opinion(0.8, 0.0, 0.5)
    assert abs(op.u - 1.0) < 1e-9


def test_calibrated_probability_requires_explicit_base_rate() -> None:
    with pytest.raises(TypeError):
        calibrated_probability_to_opinion(0.8, 10.0)


def test_calibrated_prob_large_n_returns_narrow() -> None:
    op = calibrated_probability_to_opinion(0.8, 1000.0, 0.5)
    assert op.u < 0.01
    assert abs(op.expectation() - 0.8) < 0.01


# --- ECE ---


def test_ece_perfect_calibration() -> None:
    ece = expected_calibration_error([1.0] * 50, [True] * 50)
    assert abs(ece) < 1e-9


def test_ece_miscalibrated() -> None:
    ece = expected_calibration_error([0.9] * 100, [True] * 50 + [False] * 50)
    assert ece > 0.3
