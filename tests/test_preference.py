"""Tests for ASPIC+ preference ordering.

Property-based tests verify formal properties from:
    Modgil, S. & Prakken, H. (2018). An abstract framework for
    argumentation with structured arguments. Def 9, Def 19.

Concrete tests verify known comparison outcomes.
"""

from __future__ import annotations

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.preference import (
    claim_strength,
    defeat_holds,
    strictly_weaker,
)


# ── Hypothesis strategies ───────────────────────────────────────────

_strengths = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
_strength_sets = st.lists(_strengths, min_size=1, max_size=5)
_comparisons = st.sampled_from(["elitist", "democratic"])
_preference_attack_types = st.sampled_from(["rebuts", "undermines"])
_unconditional_attack_types = st.sampled_from(["undercuts", "supersedes"])

_PROP_SETTINGS = settings(max_examples=200, deadline=None)


# ── Concrete tests: strictly_weaker ─────────────────────────────────


class TestStrictlyWeakerConcrete:
    """Concrete examples for set comparison (Def 19)."""

    def test_elitist_weaker(self):
        """Elitist: {1,5} < {3,4} because 1 < 3 and 1 < 4."""
        assert strictly_weaker([1, 5], [3, 4], "elitist") is True

    def test_elitist_not_weaker(self):
        """Elitist: {3,5} NOT < {3,4} because no element of {3,5} is < all of {3,4}."""
        assert strictly_weaker([3, 5], [3, 4], "elitist") is False

    def test_democratic_weaker(self):
        """Democratic: {1,2} < {3,4} because 1<3 and 2<4."""
        assert strictly_weaker([1, 2], [3, 4], "democratic") is True

    def test_democratic_not_weaker(self):
        """Democratic: {1,5} NOT < {3,4} because 5 has no dominator."""
        assert strictly_weaker([1, 5], [3, 4], "democratic") is False

    def test_equal_sets_not_weaker(self):
        """Equal sets are not strictly weaker under either comparison."""
        assert strictly_weaker([3, 3], [3, 3], "elitist") is False
        assert strictly_weaker([3, 3], [3, 3], "democratic") is False

    def test_singleton_comparison(self):
        """Single-element sets: both comparisons reduce to element comparison."""
        assert strictly_weaker([1], [2], "elitist") is True
        assert strictly_weaker([1], [2], "democratic") is True
        assert strictly_weaker([2], [1], "elitist") is False
        assert strictly_weaker([2], [1], "democratic") is False

    def test_empty_set_a_not_weaker(self):
        """Empty set A is not strictly weaker (neutral case, both comparisons)."""
        assert strictly_weaker([], [3, 4], "elitist") is False
        assert strictly_weaker([], [3, 4], "democratic") is False

    def test_empty_set_a_democratic_not_weaker(self):
        """Empty attacker strengths should not lose attacks under democratic comparison."""
        assert strictly_weaker([], [1.0], "democratic") is False

    def test_empty_set_b_not_dominated(self):
        """Empty set B: elitist requires exists x forall y in {} which is vacuously true.
        Democratic requires forall x exists y in {} which is false (no y)."""
        assert strictly_weaker([1, 2], [], "elitist") is True  # exists 1, forall y in {} vacuously true
        assert strictly_weaker([1, 2], [], "democratic") is False  # no y to dominate


# ── Concrete tests: defeat_holds ────────────────────────────────────


class TestDefeatHoldsConcrete:
    """Concrete examples for defeat computation (Def 9)."""

    def test_undercut_always_defeats(self):
        """Undercutting always succeeds regardless of strength."""
        assert defeat_holds("undercuts", [0.1], [0.9], "elitist") is True
        assert defeat_holds("undercuts", [0.1], [0.9], "democratic") is True

    def test_supersedes_always_defeats(self):
        """Supersedes always succeeds."""
        assert defeat_holds("supersedes", [0.1], [0.9], "elitist") is True

    def test_rebut_blocked_when_weaker(self):
        """Rebutting by strictly weaker argument does not defeat."""
        assert defeat_holds("rebuts", [1], [5], "elitist") is False

    def test_rebut_succeeds_when_stronger(self):
        """Rebutting by stronger argument defeats."""
        assert defeat_holds("rebuts", [5], [1], "elitist") is True

    def test_rebut_succeeds_when_equal(self):
        """Equal-strength rebuttal succeeds (not strictly weaker)."""
        assert defeat_holds("rebuts", [3], [3], "elitist") is True

    def test_undermine_blocked_when_weaker(self):
        """Undermining by strictly weaker argument does not defeat."""
        assert defeat_holds("undermines", [1], [5], "democratic") is False

    def test_undermine_succeeds_when_equal(self):
        """Equal-strength undermining succeeds."""
        assert defeat_holds("undermines", [3], [3], "democratic") is True


# ── Concrete tests: claim_strength ──────────────────────────────────


class TestClaimStrengthConcrete:
    """Concrete examples for claim strength computation."""

    def test_larger_sample_stronger(self):
        """Claim with larger sample_size is stronger (single-dim comparison)."""
        a = claim_strength({"sample_size": 1000})
        b = claim_strength({"sample_size": 10})
        # Both single-dim, direct element comparison
        assert a[0] > b[0]

    def test_lower_uncertainty_stronger(self):
        """Claim with lower uncertainty is stronger (single-dim comparison)."""
        a = claim_strength({"uncertainty": 0.01})
        b = claim_strength({"uncertainty": 0.5})
        assert a[0] > b[0]

    def test_missing_metadata_not_zero(self):
        """Missing metadata produces neutral strength, not zero."""
        s = claim_strength({})
        assert all(d >= 0.0 for d in s)

    def test_higher_confidence_stronger(self):
        """Higher confidence claim is stronger (all else equal)."""
        a = claim_strength({"confidence": 0.95, "sample_size": 100})
        b = claim_strength({"confidence": 0.55, "sample_size": 100})
        # Same dimensions, mean should be higher for a
        assert sum(a) / len(a) > sum(b) / len(b)

    def test_empty_claim_has_default(self):
        """Completely empty claim gets a default strength list."""
        s = claim_strength({})
        assert isinstance(s, list)
        assert len(s) >= 1


# ── Property tests ──────────────────────────────────────────────────


class TestStrictlyWeakerProperties:
    """Property tests for set comparison (Def 19)."""

    @given(_strength_sets)
    @_PROP_SETTINGS
    def test_irreflexive(self, s):
        """P1: No set is strictly weaker than itself."""
        assert strictly_weaker(s, s, "elitist") is False
        assert strictly_weaker(s, s, "democratic") is False

    @given(_strength_sets, _strength_sets, _comparisons)
    @_PROP_SETTINGS
    def test_asymmetric(self, a, b, cmp):
        """P2: If a < b then not b < a."""
        if strictly_weaker(a, b, cmp):
            assert strictly_weaker(b, a, cmp) is False

    @given(st.lists(_strengths, min_size=1, max_size=1),
           st.lists(_strengths, min_size=1, max_size=1))
    @_PROP_SETTINGS
    def test_singletons_agree(self, a, b):
        """P7: For singletons, elitist == democratic == element comparison."""
        e = strictly_weaker(a, b, "elitist")
        d = strictly_weaker(a, b, "democratic")
        assert e == d


class TestDefeatHoldsProperties:
    """Property tests for defeat computation (Def 9)."""

    @given(_strength_sets, _strength_sets, _comparisons, _unconditional_attack_types)
    @_PROP_SETTINGS
    def test_unconditional_always_defeats(self, a, b, cmp, attack_type):
        """P3/P4: Undercutting and supersedes always produce defeat."""
        assert defeat_holds(attack_type, a, b, cmp) is True

    @given(_strength_sets, _strength_sets, _comparisons, _preference_attack_types)
    @_PROP_SETTINGS
    def test_weaker_attacker_blocked(self, a, b, cmp, attack_type):
        """P5: Rebut/undermine fails when attacker is strictly weaker."""
        assume(strictly_weaker(a, b, cmp))
        assert defeat_holds(attack_type, a, b, cmp) is False

    @given(_strength_sets, _comparisons, _preference_attack_types)
    @_PROP_SETTINGS
    def test_equal_strength_succeeds(self, s, cmp, attack_type):
        """P6: Equal-strength rebuttal/undermining succeeds."""
        assert defeat_holds(attack_type, s, s, cmp) is True


class TestClaimStrengthProperties:
    """Property tests for claim_strength."""

    @given(st.fixed_dictionaries({}, optional={
        "sample_size": st.integers(min_value=1, max_value=100000),
        "uncertainty": st.floats(min_value=0.001, max_value=10.0, allow_nan=False),
        "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    }))
    @_PROP_SETTINGS
    def test_non_negative(self, claim):
        """P8: claim_strength dimensions are non-negative for all valid claims."""
        dims = claim_strength(claim)
        assert isinstance(dims, list)
        assert all(d >= 0.0 for d in dims)


class TestClaimStrengthNormalization:
    def test_multi_signal_not_inflated(self):
        """Adding a weak signal should not inflate strength past the strongest single signal.

        With multi-dim return, each dimension is independent so this checks
        that adding a weak dimension doesn't inflate the mean.
        """
        dims_unc = claim_strength({"uncertainty": 0.01})  # single dim
        dims_both = claim_strength({"uncertainty": 0.01, "confidence": 0.9})  # two dims
        # Mean of multi-dim should be less than single strong dimension
        mean_unc = sum(dims_unc) / len(dims_unc)
        mean_both = sum(dims_both) / len(dims_both)
        assert mean_both < mean_unc

    def test_same_signals_preserve_ordering(self):
        """Claims with the same signal set preserve relative ordering after normalization."""
        a = claim_strength({"sample_size": 1000, "uncertainty": 0.1})
        b = claim_strength({"sample_size": 100, "uncertainty": 0.5})
        # Both have same dimensions, mean of a should be > mean of b
        assert sum(a) / len(a) > sum(b) / len(b)


# ── Multi-dimensional claim_strength tests ─────────────────────────


class TestClaimStrengthMultiDim:
    """Tests for multi-dimensional claim_strength return.

    Per Modgil & Prakken (2018, Def 19), set comparison operates on
    multi-element sets. claim_strength returns list[float] with each
    signal as a separate dimension.
    """

    def test_claim_strength_returns_list(self):
        """claim_strength returns a list, not a scalar."""
        result = claim_strength({"sample_size": 100, "confidence": 0.9})
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_claim_strength_dimensions_independent(self):
        """Each dimension corresponds to one signal independently.

        A claim with high sample_size but low confidence should have
        dimensions that reflect this — one high, one low.
        """
        dims = claim_strength({"sample_size": 10000, "confidence": 0.1})
        assert isinstance(dims, list)
        assert len(dims) == 2
        # One dimension should be high (sample_size log-scaled) and
        # one should be low (confidence = 0.1)
        assert max(dims) > 1.0  # log1p(10000) is large
        assert min(dims) < 0.5  # confidence 0.1 is low

    def test_elitist_vs_democratic_diverge(self):
        """Elitist and democratic set comparison must produce different results.

        Per Modgil & Prakken (2018, Def 19):
        - Elitist: EXISTS x in A s.t. FORALL y in B: x < y (A has a universally weak point)
        - Democratic: FORALL x in A, EXISTS y in B: x < y (every point of A is beaten)

        With A = [3, 1] and B = [2, 2]:
        - Elitist: x=1: 1<2 AND 1<2 => YES => A IS strictly weaker
        - Democratic: x=3: exists y in {2,2} s.t. 3<y? NO => A is NOT strictly weaker

        This divergence is only possible with multi-element lists. With single-element
        lists (the old scalar behavior), elitist and democratic are always identical.
        """
        a = [3.0, 1.0]
        b = [2.0, 2.0]
        assert strictly_weaker(a, b, "elitist") is True
        assert strictly_weaker(a, b, "democratic") is False

    def test_elitist_democratic_diverge_from_claims(self):
        """End-to-end: two claims where elitist and democratic defeat differ.

        Claim A: high sample_size, low confidence => [high_dim, low_dim]
        Claim B: moderate sample_size, moderate confidence => [mod_dim, mod_dim]

        Under elitist, A's low confidence dimension makes it strictly weaker.
        Under democratic, A's high sample_size dimension saves it.
        """
        claim_a = {"sample_size": 10000, "confidence": 0.1}
        claim_b = {"sample_size": 50, "confidence": 0.5}
        dims_a = claim_strength(claim_a)
        dims_b = claim_strength(claim_b)
        assert isinstance(dims_a, list)
        assert isinstance(dims_b, list)
        assert len(dims_a) == 2
        assert len(dims_b) == 2
        # A's sample_size dimension should dominate B's
        # A's confidence dimension should be weaker than B's
        # So elitist (has a weak point) and democratic (every point beaten) should differ
        eli = strictly_weaker(dims_a, dims_b, "elitist")
        dem = strictly_weaker(dims_a, dims_b, "democratic")
        assert eli != dem  # They must diverge

    def test_maxsat_scalar_aggregation(self):
        """Scalar weight for MaxSMT is a reasonable single number derived from all dimensions.

        The mean of all dimensions preserves existing behavior for single-dim case.
        """
        dims = claim_strength({"sample_size": 100, "confidence": 0.8})
        scalar = sum(dims) / len(dims)
        assert isinstance(scalar, float)
        assert scalar > 0.0

    def test_neutral_claim_dimensions(self):
        """Claim with no metadata returns list of neutral values [1.0]."""
        result = claim_strength({})
        assert isinstance(result, list)
        assert result == [1.0]

    def test_single_dim_backward_compat(self):
        """Claims with only one signal produce valid single-element lists.

        These work correctly with defeat_holds (which already accepts list[float]).
        """
        result = claim_strength({"confidence": 0.7})
        assert isinstance(result, list)
        assert len(result) == 1
        # Single-element lists should work with defeat_holds
        assert defeat_holds("rebuts", result, [0.5], "elitist") is True  # 0.7 not weaker than 0.5
        assert defeat_holds("rebuts", [0.5], result, "elitist") is False  # 0.5 IS strictly weaker than 0.7
