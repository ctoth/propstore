"""The propstore PrAF value layer: argument/relation opinions over doxa.

These cover the propstore deltas over the formal PrAF kernel — deriving
argument- and relation-existence opinions from calibrated claim/stance fields,
paired with typed provenance, and the honest :class:`NoCalibration` returned when
calibration is absent. The opinion algebra itself is doxa's; the kernel
acceptance algorithms are the argumentation package's.
"""

from __future__ import annotations

import pytest
from argumentation.core.dung import ArgumentationFramework
from argumentation.probabilistic.probabilistic import (
    ProbabilisticAF,
    compute_probabilistic_acceptance,
)
from doxa import Opinion

from propstore.opinion_provenance import OpinionWithProvenance
from propstore.praf import (
    NoCalibration,
    PropstorePrAF,
    p_arg_from_claim,
    p_defeat_from_stance,
    p_relation_from_stance,
)
from propstore.provenance import Provenance, ProvenanceStatus


def _prior(a: float = 0.62) -> dict[str, float]:
    return {"b": 0.0, "d": 0.0, "u": 1.0, "a": a}


def _vacuous() -> Provenance:
    return Provenance(status=ProvenanceStatus.VACUOUS)


# --- p_arg_from_claim -------------------------------------------------------


def test_p_arg_from_claim_reads_explicit_opinion_columns() -> None:
    result = p_arg_from_claim(
        {
            "opinion_belief": 0.6,
            "opinion_disbelief": 0.1,
            "opinion_uncertainty": 0.3,
            "opinion_base_rate": 0.5,
        }
    )
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion == Opinion(0.6, 0.1, 0.3, 0.5)
    assert result.provenance.status is ProvenanceStatus.STATED


def test_p_arg_from_claim_opinion_columns_require_base_rate() -> None:
    result = p_arg_from_claim(
        {"opinion_belief": 0.6, "opinion_disbelief": 0.1, "opinion_uncertainty": 0.3}
    )
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_base_rate"
    assert result.missing_fields == ("opinion_base_rate",)


def test_p_arg_from_claim_without_structured_fields_is_uncalibrated() -> None:
    result = p_arg_from_claim({"claim_id": "c1", "concept": "temp"})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_claim_calibration"


def test_p_arg_from_claim_uses_prior_when_no_claim_evidence() -> None:
    result = p_arg_from_claim({"source_prior_base_rate": _prior(0.62)})
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion == Opinion(**_prior(0.62))
    assert result.provenance.status is ProvenanceStatus.STATED


def test_p_arg_from_claim_builds_claim_evidence_opinion() -> None:
    result = p_arg_from_claim(
        {
            "source_prior_base_rate": _prior(0.62),
            "claim_probability": 0.8,
            "effective_sample_size": 10,
        }
    )
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion == Opinion.from_probability(0.8, 10, 0.62)
    assert result.provenance.status is ProvenanceStatus.CALIBRATED


def test_p_arg_from_claim_discounts_by_source_quality() -> None:
    quality = {"b": 0.7, "d": 0.1, "u": 0.2, "a": 0.5}
    result = p_arg_from_claim(
        {
            "source_prior_base_rate": _prior(0.62),
            "claim_probability": 0.8,
            "effective_sample_size": 10,
            "source_quality_opinion": quality,
        }
    )
    expected = Opinion(0.7, 0.1, 0.2, 0.5).discount(Opinion.from_probability(0.8, 10, 0.62))
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion == expected


def test_p_arg_from_claim_requires_prior_for_claim_evidence() -> None:
    result = p_arg_from_claim({"claim_probability": 0.8, "effective_sample_size": 10})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_base_rate"
    assert "source_prior_base_rate" in result.missing_fields


def test_p_arg_from_claim_ignores_sample_size_without_calibration() -> None:
    result = p_arg_from_claim({"sample_size": 50})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_claim_calibration"


def test_p_arg_from_claim_rejects_invalid_quality_shape() -> None:
    with pytest.raises(ValueError, match="b, d, u, and a"):
        p_arg_from_claim(
            {"source_prior_base_rate": _prior(0.62), "source_quality_opinion": {"b": 0.7}}
        )


def test_p_arg_from_claim_reads_nested_source_trust() -> None:
    result = p_arg_from_claim(
        {"source": {"trust": {"prior_base_rate": _prior(0.4)}}}
    )
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion == Opinion(**_prior(0.4))


# --- p_relation_from_stance / p_defeat_from_stance --------------------------


def test_p_relation_reads_opinion_columns() -> None:
    result = p_relation_from_stance(
        {
            "opinion_belief": 0.7,
            "opinion_disbelief": 0.1,
            "opinion_uncertainty": 0.2,
            "opinion_base_rate": 0.5,
            "confidence": 0.8,
        }
    )
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion.b == pytest.approx(0.7)
    assert result.opinion.u == pytest.approx(0.2)
    assert result.provenance.status is ProvenanceStatus.STATED


def test_p_relation_confidence_needs_evidence_count() -> None:
    result = p_relation_from_stance({"confidence": 0.75, "opinion_base_rate": 0.5})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_evidence_count"
    assert result.missing_fields == ("effective_sample_size", "sample_size")


def test_p_relation_confidence_with_sample_size_is_calibrated() -> None:
    result = p_relation_from_stance(
        {"confidence": 0.75, "effective_sample_size": 10, "opinion_base_rate": 0.5}
    )
    assert isinstance(result, OpinionWithProvenance)
    assert result.opinion.expectation() == pytest.approx(0.75, abs=0.05)


def test_p_relation_zero_confidence_is_uncalibrated() -> None:
    result = p_relation_from_stance({"confidence": 0.0})
    assert isinstance(result, NoCalibration)
    assert result.reason == "zero_confidence_without_opinion"


def test_p_relation_empty_is_uncalibrated() -> None:
    result = p_relation_from_stance({})
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_relation_calibration"


def test_p_relation_columns_require_base_rate() -> None:
    result = p_relation_from_stance(
        {"opinion_belief": 0.5, "opinion_disbelief": 0.3, "opinion_uncertainty": 0.2}
    )
    assert isinstance(result, NoCalibration)
    assert result.reason == "missing_base_rate"
    assert result.missing_fields == ("opinion_base_rate",)


def test_p_defeat_from_stance_is_the_relation_rule() -> None:
    stance = {"confidence": 0.6, "effective_sample_size": 8, "opinion_base_rate": 0.5}
    assert p_defeat_from_stance(stance) == p_relation_from_stance(stance)


# --- kernel integration + frozen immutability -------------------------------


def test_kernel_acceptance_over_deterministic_chain() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c")}),
    )
    kernel = ProbabilisticAF(
        framework=framework,
        p_args={"a": 1.0, "b": 1.0, "c": 1.0},
        p_defeats={("a", "b"): 1.0, ("b", "c"): 1.0},
    )
    result = compute_probabilistic_acceptance(kernel, semantics="grounded")
    assert result.acceptance_probs is not None
    assert result.acceptance_probs["a"] == pytest.approx(1.0)
    assert result.acceptance_probs["b"] == pytest.approx(0.0)
    assert result.acceptance_probs["c"] == pytest.approx(1.0)


def test_propstore_praf_omission_maps_are_immutable() -> None:
    framework = ArgumentationFramework(arguments=frozenset({"a"}), defeats=frozenset())
    praf = PropstorePrAF(
        kernel=ProbabilisticAF(framework=framework, p_args={"a": 0.5}, p_defeats={}),
        p_args={"a": OpinionWithProvenance(Opinion.vacuous(0.5), _vacuous())},
        p_defeats={},
        omitted_arguments={"a": NoCalibration("missing_claim_calibration")},
    )
    with pytest.raises(TypeError):
        praf.omitted_arguments["b"] = NoCalibration("mutated")  # type: ignore[index]
