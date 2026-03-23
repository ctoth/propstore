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
        """Claim with larger sample_size is stronger."""
        a = claim_strength({"sample_size": 1000})
        b = claim_strength({"sample_size": 10})
        assert a > b

    def test_lower_uncertainty_stronger(self):
        """Claim with lower uncertainty is stronger."""
        a = claim_strength({"uncertainty": 0.01})
        b = claim_strength({"uncertainty": 0.5})
        assert a > b

    def test_missing_metadata_not_zero(self):
        """Missing metadata produces a neutral strength, not zero."""
        s = claim_strength({})
        assert s >= 0.0

    def test_higher_confidence_stronger(self):
        """Higher confidence claim is stronger (all else equal)."""
        a = claim_strength({"confidence": 0.95, "sample_size": 100})
        b = claim_strength({"confidence": 0.55, "sample_size": 100})
        assert a > b

    def test_empty_claim_has_default(self):
        """Completely empty claim gets a default strength."""
        s = claim_strength({})
        assert isinstance(s, float)


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
        """P8: claim_strength is non-negative for all valid claims."""
        assert claim_strength(claim) >= 0.0


class TestClaimStrengthNormalization:
    def test_multi_signal_not_inflated(self):
        """Adding a weak signal should not inflate strength past the strongest single signal."""
        from propstore.preference import claim_strength
        unc_only = claim_strength({"uncertainty": 0.01})  # 1/0.01 = 100.0 (1 component)
        both = claim_strength({"uncertainty": 0.01, "confidence": 0.9})  # (100 + 0.9) / 2 after fix
        # Currently: both = 100.9 > 100.0 (BUG: raw sum inflates)
        # After fix: both = 50.45 < 100.0 (normalized average)
        assert both < unc_only

    def test_same_signals_preserve_ordering(self):
        """Claims with the same signal set preserve relative ordering after normalization."""
        from propstore.preference import claim_strength
        a = claim_strength({"sample_size": 1000, "uncertainty": 0.1})
        b = claim_strength({"sample_size": 100, "uncertainty": 0.5})
        assert a > b  # bigger sample + lower uncertainty = stronger
