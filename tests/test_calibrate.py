"""Tests for propstore.heuristic.calibrate — calibration module."""

import math
import sqlite3

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.heuristic.calibrate import (
    CalibrationSource,
    CorpusCalibrator,
    CategoryPrior,
    TemperatureScaler,
    calibrated_probability_to_opinion,
    categorical_to_opinion,
    expected_calibration_error,
)
from propstore.core.base_rates import BaseRateUnresolved
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus
from tests.conftest import create_argumentation_schema, insert_claim, insert_stance


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
    cal = CorpusCalibrator([0.1, 0.3, 0.5, 0.7, 0.9], corpus_base_rate=0.5)
    # Below min
    assert 0.0 <= cal.percentile(0.0) <= 1.0
    # Above max
    assert 0.0 <= cal.percentile(10.0) <= 1.0
    # In range
    assert 0.0 <= cal.percentile(0.5) <= 1.0


def test_corpus_calibrator_monotonicity():
    """Smaller distance -> smaller percentile (more similar)."""
    cal = CorpusCalibrator(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        corpus_base_rate=0.5,
    )
    p1 = cal.percentile(0.2)
    p2 = cal.percentile(0.8)
    assert p1 <= p2


def test_corpus_calibrator_requires_explicit_base_rate():
    with pytest.raises(TypeError):
        CorpusCalibrator([0.1, 0.2, 0.3])


def test_corpus_calibrator_from_cdf_requires_explicit_base_rate():
    with pytest.raises(TypeError):
        CorpusCalibrator.from_cdf([0.1, 0.2, 0.3])


def test_corpus_calibrator_uncertainty_scales_with_n():
    """Opinion uncertainty should scale approximately as 1/sqrt(n).

    More reference points -> narrower (less uncertain) opinion.
    """
    small_ref = [float(i) / 10 for i in range(10)]
    large_ref = [float(i) / 1000 for i in range(1000)]

    cal_small = CorpusCalibrator(small_ref, corpus_base_rate=0.5)
    cal_large = CorpusCalibrator(large_ref, corpus_base_rate=0.5)

    op_small = cal_small.to_opinion(0.05)
    op_large = cal_large.to_opinion(0.05)

    # Larger corpus should give less uncertainty
    assert op_large.u < op_small.u


# ---------------------------------------------------------------------------
# Categorical to Opinion
# ---------------------------------------------------------------------------


def test_categorical_without_prior_returns_unresolved():
    """Without a sourced prior, no numeric opinion is produced."""
    result = categorical_to_opinion("strong", 1)
    assert isinstance(result, BaseRateUnresolved)
    assert result.reason == "missing_base_rate"


def test_categorical_with_calibration_returns_informative():
    """With calibration counts, opinion should be informative (u < 1.0)."""
    counts = {
        (1, "strong"): (80, 100),
        (1, "moderate"): (60, 100),
    }
    op = categorical_to_opinion(
        "strong",
        1,
        calibration_counts=counts,
        prior=_category_prior("strong"),
    )
    assert isinstance(op, Opinion)
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
    op = calibrated_probability_to_opinion(0.8, 0.0, 0.5)
    assert abs(op.u - 1.0) < 1e-9


def test_calibrated_probability_requires_explicit_base_rate():
    with pytest.raises(TypeError):
        calibrated_probability_to_opinion(0.8, 10.0)


def test_calibrated_prob_large_n_returns_narrow():
    """Large n should give narrow opinion near the probability."""
    op = calibrated_probability_to_opinion(0.8, 1000.0, 0.5)
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
    op = categorical_to_opinion(
        "strong",
        1,
        calibration_counts=counts,
        prior=_category_prior("strong"),
    )
    assert isinstance(op, Opinion)
    # r=85, s=15 -> b=85/102, d=15/102, u=2/102
        # expectation = b + a*u = 85/102 + 0.5 * 2/102
    # The empirical prob is 85/100 = 0.85
    # With W=2 and no explicit CategoryPrior, expectation = (85 + 0.5*2) / 102.
    expected_emp = (85 + 0.5 * 2) / 102
    assert abs(op.expectation() - expected_emp) < 1e-6


# ---------------------------------------------------------------------------
# Red-phase tests: calibration evidence model invariants (F4, F10, M8)
# ---------------------------------------------------------------------------


class TestCorpusCalibrationEvidenceModel:
    """Tests exposing that corpus size is NOT claim-level evidence.

    Finding 4 (audit-opinion-algebra.md): CorpusCalibrator.to_opinion passes
    full corpus size as effective sample size n to from_probability(). A corpus
    of 10,000 pairwise distances produces u = 2/(10000+2) ~ 0.0002 — near-
    dogmatic certainty. But corpus size measures distribution coverage, not
    evidence for any individual claim. Per Josang 2001 (p.8) and the project
    principle "honest ignorance over fabricated confidence", this is wrong.
    """

    @pytest.mark.property
    @given(
        distance=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings()
    def test_large_corpus_does_not_produce_near_dogmatic_opinion(
        self, distance: float
    ):
        """A 10,000-element corpus calibrator must NOT produce near-dogmatic
        opinions (u < 0.01). Corpus size is evidence for the calibration of
        the distance metric, not evidence for the truth of any claim.

        Per Josang 2001 (p.8): u ~ 0 means near-absolute certainty.
        Per Sensoy 2018 (p.3-4): evidence counts represent actual observations
        supporting a class — not corpus distribution statistics.

        EXPECTED TO FAIL: current code produces u = 2/(10000+2) ~ 0.0002.
        """
        # Build a large corpus of uniformly spaced reference distances
        ref = [i / 10_000 for i in range(10_000)]
        cal = CorpusCalibrator(ref, corpus_base_rate=0.5)
        opinion = cal.to_opinion(distance)

        # u > 0.01: the system should NOT be 99%+ certain about a claim
        # just because it has a large reference corpus
        assert opinion.u > 0.01, (
            f"Near-dogmatic opinion u={opinion.u:.6f} from corpus of 10,000 "
            f"distances. Corpus size is not claim-level evidence."
        )

    def test_single_element_corpus_produces_near_vacuous_opinion(self):
        """A single-reference-point corpus has almost no calibration data.
        The resulting opinion should be near-vacuous (u > 0.9), honestly
        representing ignorance.

        Per Josang 2001 (p.8): vacuous opinion (0,0,1,a) = total ignorance.
        With only 1 data point, the system knows almost nothing about the
        distance distribution.
        """
        cal = CorpusCalibrator([0.5], corpus_base_rate=0.5)
        opinion = cal.to_opinion(0.3)

        assert opinion.u > 0.9, (
            f"Single-element corpus produced opinion with u={opinion.u:.4f}. "
            f"Expected near-vacuous (u > 0.9) per honest ignorance principle."
        )

    @pytest.mark.property
    @given(
        n=st.integers(min_value=1, max_value=500),
        distance=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings()
    def test_opinion_bdu_sum_invariant(self, n: int, distance: float):
        """b + d + u = 1.0 must hold for all calibrator outputs.

        Per Josang 2001 (Def 9, p.7): this is the fundamental constraint.
        The Opinion constructor enforces this, so this should PASS.
        """
        ref = [i / max(n, 1) for i in range(n)]
        cal = CorpusCalibrator(ref, corpus_base_rate=0.5)
        op = cal.to_opinion(distance)

        total = op.b + op.d + op.u
        assert abs(total - 1.0) < 1e-9, (
            f"b + d + u = {total} != 1.0 for n={n}, distance={distance}"
        )

    def test_monotonic_evidence_uncertainty_relationship(self):
        """More corpus data should produce less uncertainty (monotonic).

        For the same query distance, a larger reference corpus should yield
        a tighter opinion. This tests the directional relationship, not the
        magnitude (which is the bug in Test 1).
        """
        sizes = [10, 100, 1000]
        distance = 0.25
        uncertainties = []

        for n in sizes:
            ref = [i / n for i in range(n)]
            cal = CorpusCalibrator(ref, corpus_base_rate=0.5)
            op = cal.to_opinion(distance)
            uncertainties.append(op.u)

        for i in range(len(uncertainties) - 1):
            assert uncertainties[i] > uncertainties[i + 1], (
                f"Uncertainty not monotonically decreasing: "
                f"u({sizes[i]})={uncertainties[i]:.6f} <= "
                f"u({sizes[i+1]})={uncertainties[i+1]:.6f}"
            )


# ---------------------------------------------------------------------------
# Red-phase tests: calibration counts infrastructure (Phase 1, Sub-task 1b)
# ---------------------------------------------------------------------------


class TestCalibrationCountsInfrastructure:
    """Tests for typed calibration count data from sidecar storage."""

    def test_categorical_to_opinion_with_typed_counts(self, tmp_path):
        """When calibration_counts are loaded from a sidecar table,
        categorical_to_opinion produces non-vacuous opinions.

        Per Josang 2001 (p.20-21, Def 12): evidence maps to opinion with
        u = 2/(r+s+2). With 80/100 accuracy, u = 2/102 ~ 0.02.
        """
        from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
        from propstore.families.calibration.declaration import (
            CalibrationCount,
            calibration_counts_by_key,
        )
        from propstore.families.registry import (
            world_schema,
        )

        sidecar_path = tmp_path / "propstore.sqlite"
        schema = world_schema()
        create_sqlalchemy_store(sidecar_path, schema)
        with writable_session(sidecar_path, schema) as derived:
            derived.session.add(
                CalibrationCount(
                    pass_number=1,
                    category="strong",
                    correct_count=80,
                    total_count=100,
                )
            )
            derived.session.commit()

        with readonly_session(sidecar_path, schema) as derived:
            counts = calibration_counts_by_key(derived)

        op = categorical_to_opinion(
            "strong",
            1,
            calibration_counts=counts,
            prior=_category_prior("strong"),
        )
        assert isinstance(op, Opinion)
        assert op.u < 0.5, (
            f"With 80/100 calibration data, uncertainty should be < 0.5, got {op.u}"
        )

    def test_calibration_count_empty_table(self, tmp_path):
        """Empty calibration_counts table returns None (honest ignorance).

        Per Josang 2001 (p.8): when no data exists, the system must represent
        total ignorance, not fabricate confidence.
        """
        from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session
        from propstore.families.calibration.declaration import calibration_counts_by_key
        from propstore.families.registry import world_schema

        sidecar_path = tmp_path / "propstore.sqlite"
        schema = world_schema()
        create_sqlalchemy_store(sidecar_path, schema)

        with readonly_session(sidecar_path, schema) as derived:
            result = calibration_counts_by_key(derived)

        assert result is None, (
            "Empty calibration_counts table should return None (honest ignorance)"
        )


# ---------------------------------------------------------------------------
# Red-phase tests: corpus opinion b+d+u=1 property (Phase 1, Sub-task 1b)
# ---------------------------------------------------------------------------


class TestCorpusOpinionBDUSumProperty:
    """Hypothesis property test: CorpusCalibrator.to_opinion must always
    produce b+d+u=1.

    Per Josang 2001 (Def 9, p.7): this is the fundamental constraint.
    This is a guard test to maintain the invariant under any input.
    """

    @pytest.mark.property
    @given(
        ref_distances=st.lists(
            st.floats(min_value=0.0, max_value=2.0),
            min_size=1,
            max_size=100,
        ),
        query_distance=st.floats(min_value=0.0, max_value=2.0),
    )
    @settings(deadline=None)
    def test_bdu_sum_is_one(self, ref_distances, query_distance):
        """b + d + u must equal 1.0 for all CorpusCalibrator outputs."""
        cal = CorpusCalibrator(ref_distances, corpus_base_rate=0.5)
        op = cal.to_opinion(query_distance)
        total = op.b + op.d + op.u
        assert abs(total - 1.0) < 1e-9, (
            f"b+d+u={total} != 1.0 for ref_distances={ref_distances[:5]}..., "
            f"query={query_distance}"
        )


class TestOpinionInvariants:
    """The ``Opinion`` type enforces Josang opinion invariants at construction.

    The relation-opinion storage no longer keeps four scalar
    ``opinion_belief/_disbelief/_uncertainty/_base_rate`` columns with SQLite
    CHECK constraints; ``relation_edge.opinion`` is a single typed column
    holding the serialized ``Opinion``. The invariants Finding 10
    (audit-opinion-algebra.md) wanted enforced — ``b+d+u=1``, ``b,d,u in
    [0,1]``, ``a in (0,1)`` — are now enforced by ``Opinion.__init__`` (the
    doxa kernel), so an invalid opinion can never be constructed, let alone
    persisted. These tests assert that enforcement at the type layer.
    """

    def test_rejects_invalid_opinion_sum(self):
        """b=0.9, d=0.9, u=0.9 violates b+d+u=1 (Josang 2001, Def 9, p.7)."""
        with pytest.raises(ValueError):
            Opinion(0.9, 0.9, 0.9, 0.5)

    def test_rejects_negative_belief(self):
        """b=-0.1 is outside [0, 1] (Josang 2001, Def 1, p.5)."""
        with pytest.raises(ValueError):
            Opinion(-0.1, 0.6, 0.5, 0.5)

    def test_rejects_base_rate_zero(self):
        """a=0.0 is outside the open interval (0, 1) (Josang 2001, Def 1, p.5)."""
        with pytest.raises(ValueError):
            Opinion(0.3, 0.2, 0.5, 0.0)

    def test_rejects_base_rate_one(self):
        """a=1.0 is outside the open interval (0, 1) (Josang 2001, Def 1, p.5)."""
        with pytest.raises(ValueError):
            Opinion(0.3, 0.2, 0.5, 1.0)

    def test_accepts_null_opinion(self):
        """A NULL opinion (no opinion attached) is accepted by the schema."""
        conn = sqlite3.connect(":memory:")
        create_argumentation_schema(conn)
        insert_claim(conn, "c1", claim_type="parameter", concept_id="concept1", value=1.0, source_paper="paper1")
        insert_claim(conn, "c2", claim_type="parameter", concept_id="concept1", value=2.0, source_paper="paper1")

        insert_stance(conn, "c1", "c2", "supports", confidence=0.8, opinion=None)

    def test_accepts_valid_opinion(self):
        """Valid b=0.3, d=0.2, u=0.5, a=0.5 constructs and persists.

        Per Josang 2001 (Def 1, p.5): b+d+u=1 and a in (0,1).
        """
        conn = sqlite3.connect(":memory:")
        create_argumentation_schema(conn)
        insert_claim(conn, "c1", claim_type="parameter", concept_id="concept1", value=1.0, source_paper="paper1")
        insert_claim(conn, "c2", claim_type="parameter", concept_id="concept1", value=2.0, source_paper="paper1")

        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.8,
            opinion=Opinion(0.3, 0.2, 0.5, 0.5),
        )
