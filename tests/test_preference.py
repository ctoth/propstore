"""Tests for propstore-owned metadata preference heuristics."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import propstore.preference as preference
from propstore.preference import claim_strength


_PROP_SETTINGS = settings(deadline=None)


class TestClaimStrengthConcrete:
    def test_metadata_strength_vector_is_honest_name_for_heuristic(self) -> None:
        claim = {"sample_size": 25, "uncertainty": 0.2, "confidence": 0.8}
        assert preference.metadata_strength_vector(claim) == claim_strength(claim)

    def test_larger_sample_stronger(self) -> None:
        a = claim_strength({"sample_size": 1000})
        b = claim_strength({"sample_size": 10})
        assert a[0] > b[0]

    def test_lower_uncertainty_stronger(self) -> None:
        a = claim_strength({"uncertainty": 0.01})
        b = claim_strength({"uncertainty": 0.5})
        assert a[1] > b[1]

    def test_higher_confidence_stronger(self) -> None:
        a = claim_strength({"confidence": 0.95, "sample_size": 100})
        b = claim_strength({"confidence": 0.55, "sample_size": 100})
        assert sum(a) / len(a) > sum(b) / len(b)

    def test_empty_claim_has_neutral_defaults(self) -> None:
        assert claim_strength({}) == [0.0, 1.0, 0.5]


class TestClaimStrengthFixedLength:
    def test_claim_strength_fixed_length_all_fields(self) -> None:
        claim = {"sample_size": 100, "uncertainty": 0.2, "confidence": 0.9}
        assert len(claim_strength(claim)) == 3

    def test_claim_strength_fixed_length_partial(self) -> None:
        result = claim_strength({"sample_size": 500})
        assert result[1] == 1.0
        assert result[2] == 0.5

    def test_claim_strength_fixed_length_different_partials(self) -> None:
        a = claim_strength({"sample_size": 100})
        b = claim_strength({"confidence": 0.8})
        assert len(a) == len(b) == 3

    def test_single_signal_vectors_are_commensurable(self) -> None:
        sample_only = claim_strength({"sample_size": 50})
        confidence_only = claim_strength({"confidence": 0.7})
        assert len(sample_only) == len(confidence_only) == 3


class TestClaimStrengthNormalization:
    def test_multi_signal_not_inflated(self) -> None:
        dims_unc = claim_strength({"uncertainty": 0.01})
        dims_both = claim_strength({"uncertainty": 0.01, "confidence": 0.9})
        assert dims_unc[1] == dims_both[1]
        assert dims_both[2] > dims_unc[2]

    def test_same_signals_preserve_ordering(self) -> None:
        a = claim_strength({"sample_size": 1000, "uncertainty": 0.1})
        b = claim_strength({"sample_size": 100, "uncertainty": 0.5})
        assert sum(a) / len(a) > sum(b) / len(b)


class TestClaimStrengthProperties:
    pytestmark = pytest.mark.property

    @given(
        st.fixed_dictionaries(
            {},
            optional={
                "sample_size": st.integers(min_value=1, max_value=100000),
                "uncertainty": st.floats(
                    min_value=0.001,
                    max_value=10.0,
                    allow_nan=False,
                    allow_infinity=False,
                ),
                "confidence": st.floats(
                    min_value=0.0,
                    max_value=1.0,
                    allow_nan=False,
                    allow_infinity=False,
                ),
            },
        )
    )
    @_PROP_SETTINGS
    def test_claim_strength_always_three_non_negative_elements(self, claim) -> None:
        dims = claim_strength(claim)
        assert len(dims) == 3
        assert all(d >= 0.0 for d in dims)
