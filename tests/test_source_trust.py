from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.opinion import Opinion, discount, from_probability
from propstore.praf import p_arg_from_claim


def test_p_arg_from_claim_uses_prior_base_rate_when_no_claim_evidence() -> None:
    opinion = p_arg_from_claim({"source_prior_base_rate": 0.62})
    assert opinion == Opinion.vacuous(a=0.62)


def test_p_arg_from_claim_builds_claim_evidence_opinion() -> None:
    opinion = p_arg_from_claim(
        {
            "source_prior_base_rate": 0.62,
            "claim_probability": 0.8,
            "effective_sample_size": 10,
        }
    )
    assert opinion == from_probability(0.8, 10, 0.62)


def test_p_arg_from_claim_discounts_claim_by_source_quality() -> None:
    claim = {
        "source_prior_base_rate": 0.62,
        "claim_probability": 0.8,
        "effective_sample_size": 10,
        "source_quality_opinion": {
            "b": 0.7,
            "d": 0.1,
            "u": 0.2,
            "a": 0.5,
        },
    }
    expected_claim = from_probability(0.8, 10, 0.62)
    expected = discount(Opinion(0.7, 0.1, 0.2, 0.5), expected_claim)
    assert p_arg_from_claim(claim) == expected


@given(
    prior=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
    probability=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    n_eff=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, deadline=None)
def test_p_arg_from_claim_expectation_stays_in_unit_interval(
    prior: float,
    probability: float,
    n_eff: float,
) -> None:
    opinion = p_arg_from_claim(
        {
            "source_prior_base_rate": prior,
            "claim_probability": probability,
            "effective_sample_size": n_eff,
        }
    )
    assert 0.0 <= opinion.expectation() <= 1.0


def test_p_arg_from_claim_rejects_invalid_source_quality_shape() -> None:
    with pytest.raises(ValueError):
        p_arg_from_claim(
            {
                "source_prior_base_rate": 0.62,
                "source_quality_opinion": {"b": 0.7},
            }
        )
