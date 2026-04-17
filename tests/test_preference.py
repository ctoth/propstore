"""Tests for ASPIC+ preference ordering.

Property-based tests verify formal properties from:
    Modgil, S. & Prakken, H. (2018). An abstract framework for
    argumentation with structured arguments. Def 9, Def 19.
    Prakken (2010), page 16, local image:
    papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png
    Lehtonen (2024), pages 523-524, local images:
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png

Concrete tests verify known comparison outcomes.
"""

from __future__ import annotations

import pytest

import propstore.preference as preference
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

_PROP_SETTINGS = settings(deadline=None)


# ── Concrete tests: strictly_weaker ─────────────────────────────────


class TestStrictlyWeakerConcrete:
    """Concrete examples for set comparison (Def 19).

    Grounding:
    - Prakken (2010), page 16:
      papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png
    - Lehtonen (2024), pages 523-524:
      papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
      papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
    """

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
        """Empty set B: nothing to be weaker than — result is False for both comparisons."""
        assert strictly_weaker([1, 2], [], "elitist") is False
        assert strictly_weaker([1, 2], [], "democratic") is False


class TestElitistEmptySetVacuousTruth:
    """Tests for Finding F16: elitist empty-set vacuous truth bug.

    Bug: strictly_weaker(anything, [], "elitist") returns True because
    all(x < y for y in []) is vacuously True. This incorrectly makes
    non-empty sets "strictly weaker" than an empty set, which blocks
    rebut/undermine attacks against targets with no strength dimensions.

    Reference: Modgil & Prakken 2018, Def 19. An empty comparison set
    has no elements to be weaker than — the result should be False.
    """

    def test_nonempty_vs_empty_elitist_not_weaker(self):
        """Non-empty set is NOT strictly weaker than empty set.

        strictly_weaker([1.0], [], "elitist") should be False.
        Nothing to be weaker than — empty set is not "stronger".
        Currently returns True due to vacuous truth of all() on empty.
        """
        assert strictly_weaker([1.0], [], "elitist") is False

    def test_empty_vs_nonempty_elitist_not_weaker(self):
        """Empty set is NOT strictly weaker than non-empty set.

        strictly_weaker([], [1.0], "elitist") should be False.
        Empty set has no elements to test — nothing is "strictly weaker".
        """
        assert strictly_weaker([], [1.0], "elitist") is False

    def test_control_normal_nonempty_elitist(self):
        """Control: normal non-empty comparison works correctly.

        strictly_weaker([0.1], [0.9], "elitist") should be True.
        0.1 < 0.9 — genuinely weaker.
        """
        assert strictly_weaker([0.1], [0.9], "elitist") is True


# ── Concrete tests: defeat_holds ────────────────────────────────────


class TestDefeatHoldsConcrete:
    """Concrete examples for defeat computation (Def 9).

    Lehtonen (2024), pages 523-524, separates preference-independent
    defeats from contradictory rebut and undermine cases controlled by
    elitist/democratic lifting:
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
    """

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

    def test_metadata_strength_vector_is_honest_name_for_heuristic(self):
        """The metadata heuristic should be available under an honest name."""
        claim = {"sample_size": 25, "uncertainty": 0.2, "confidence": 0.8}
        assert preference.metadata_strength_vector(claim) == claim_strength(claim)

    def test_larger_sample_stronger(self):
        """Claim with larger sample_size is stronger (single-dim comparison)."""
        a = claim_strength({"sample_size": 1000})
        b = claim_strength({"sample_size": 10})
        # Both single-dim, direct element comparison
        assert a[0] > b[0]

    def test_lower_uncertainty_stronger(self):
        """Claim with lower uncertainty is stronger (inverse_uncertainty dimension)."""
        a = claim_strength({"uncertainty": 0.01})
        b = claim_strength({"uncertainty": 0.5})
        assert a[1] > b[1]  # inverse_uncertainty is dimension [1]

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
    """Property tests for set comparison (Def 19).

    Prakken (2010), page 16, states the elitist set order used by
    last-link:
    papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png

    Lehtonen (2024), pages 523-524, rephrases last-link defeat under
    elitist and democratic lifting:
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
    """

    pytestmark = pytest.mark.property

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

    @given(
        low=st.integers(min_value=0, max_value=100),
        first_gap=st.integers(min_value=1, max_value=50),
        second_gap=st.integers(min_value=1, max_value=50),
    )
    @_PROP_SETTINGS
    def test_generated_elitist_democratic_divergence(self, low, first_gap, second_gap):
        """Generated multi-element sets can force lifting divergence.

        Let low < mid < high, A = {high, low}, and B = {mid, mid}.
        Elitist lifting says A < B because low is below every member of B.
        Democratic lifting says A is not < B because high is not below any
        member of B.

        Grounding:
        papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
        """
        mid = low + first_gap
        high = mid + second_gap
        attacker = [float(high), float(low)]
        target = [float(mid), float(mid)]

        assert strictly_weaker(attacker, target, "elitist") is True
        assert strictly_weaker(attacker, target, "democratic") is False


class TestDefeatHoldsProperties:
    """Property tests for defeat computation (Def 9).

    Preference-independent undercuts and preference-dependent rebut or
    undermine behavior follow the Lehtonen (2024) last-link rephrasing:
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
    papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
    """

    pytestmark = pytest.mark.property

    @given(_strength_sets, _strength_sets, _comparisons, _unconditional_attack_types)
    @_PROP_SETTINGS
    def test_unconditional_always_defeats(self, a, b, cmp, attack_type):
        """P3/P4: Undercutting and supersedes always produce defeat."""
        assert defeat_holds(attack_type, a, b, cmp) is True

    @given(_strength_sets, _strength_sets)
    @_PROP_SETTINGS
    def test_undercut_is_preference_independent(self, a, b):
        """Undercut defeat is independent of elitist/democratic lifting.

        Lehtonen (2024), page 523, classifies undercutting as
        preference-independent in the last-link rephrasing:
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png
        """
        assert defeat_holds("undercuts", a, b, "elitist") is True
        assert defeat_holds("undercuts", a, b, "democratic") is True

    @given(_strength_sets, _strength_sets, _comparisons, _preference_attack_types)
    @_PROP_SETTINGS
    def test_weaker_attacker_blocked(self, a, b, cmp, attack_type):
        """P5: Rebut/undermine fails when attacker is strictly weaker."""
        assume(strictly_weaker(a, b, cmp))
        assert defeat_holds(attack_type, a, b, cmp) is False

    @given(_strength_sets, _comparisons, _preference_attack_types)
    @_PROP_SETTINGS
    def test_equal_strength_succeeds(self, s, cmp, attack_type):
        """P6: Equal-strength rebuttal/undermining succeeds.

        Equal strengths are not strictly weaker, so contradictory rebut
        and undermine attacks are not blocked by lifting:
        papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png
        """
        assert defeat_holds(attack_type, s, s, cmp) is True


class TestClaimStrengthProperties:
    """Property tests for claim_strength."""

    pytestmark = pytest.mark.property

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
        """Adding a weak signal should not inflate the strong dimension.

        With fixed-length 3-element vectors, each dimension is independent.
        The inverse_uncertainty dimension should be the same regardless of
        whether confidence is also provided.
        """
        dims_unc = claim_strength({"uncertainty": 0.01})
        dims_both = claim_strength({"uncertainty": 0.01, "confidence": 0.9})
        # inverse_uncertainty dimension [1] should be identical
        assert dims_unc[1] == dims_both[1]
        # confidence dimension [2] differs: default 0.5 vs provided 0.9
        assert dims_both[2] > dims_unc[2]

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
        Fixed-length: [log_sample_size, inverse_uncertainty, confidence].
        """
        dims = claim_strength({"sample_size": 10000, "confidence": 0.1})
        assert isinstance(dims, list)
        assert len(dims) == 3
        # log_sample_size dimension should be high
        assert dims[0] > 1.0  # log1p(10000) is large
        # confidence dimension should be low
        assert dims[2] < 0.5  # confidence 0.1 is low

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

        Claim A: high sample_size, low confidence => high dim[0], low dim[2]
        Claim B: moderate sample_size, moderate confidence => mod dim[0], mod dim[2]

        Under elitist, A's low confidence dimension makes it strictly weaker.
        Under democratic, A's high sample_size dimension saves it.

        Fixed-length 3-element vectors: both have same inverse_uncertainty
        default (1.0), so divergence comes from dim[0] vs dim[2].
        """
        claim_a = {"sample_size": 10000, "confidence": 0.1}
        claim_b = {"sample_size": 50, "confidence": 0.5}
        dims_a = claim_strength(claim_a)
        dims_b = claim_strength(claim_b)
        assert isinstance(dims_a, list)
        assert isinstance(dims_b, list)
        assert len(dims_a) == 3
        assert len(dims_b) == 3
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
        """Claim with no metadata returns 3-element vector of neutral defaults."""
        result = claim_strength({})
        assert isinstance(result, list)
        assert result == [0.0, 1.0, 0.5]

    def test_single_signal_backward_compat(self):
        """Claims with one signal produce fixed-length 3-element vectors.

        These work correctly with defeat_holds (which accepts list[float]).
        The confidence-only claim gets defaults for the other two dimensions.

        With fixed-length vectors, two claims differing only in confidence
        share identical dim[0] and dim[1]. Neither is strictly weaker under
        elitist or democratic comparison because shared dimensions tie.
        This is correct: single-dimension differences are not enough to
        establish strict weakness across all 3 dimensions.
        """
        result = claim_strength({"confidence": 0.7})
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[2] == 0.7  # confidence in dimension [2]
        # Fixed-length vectors work with defeat_holds without crashing
        weak = claim_strength({"confidence": 0.3})
        assert len(weak) == 3
        assert weak[2] == 0.3
        # Both rebuts succeed: neither is strictly weaker (shared dims tie)
        assert defeat_holds("rebuts", result, weak, "elitist") is True
        assert defeat_holds("rebuts", weak, result, "elitist") is True


# ── Phase 3: Fixed-length preference vector tests ──────────────────
#
# These tests assert that claim_strength() ALWAYS returns a 3-element
# vector with neutral defaults for missing dimensions, so that
# strictly_weaker() comparisons between claims with different metadata
# profiles are commensurable.
#
# Neutral defaults rationale:
#   [0] log_sample_size: 0.0  — log1p(0) = 0, "no samples observed"
#   [1] inverse_uncertainty: 1.0 — 1/1.0 = 1.0, "maximum uncertainty"
#   [2] confidence: 0.5 — coin flip, neither advantage nor disadvantage
#
# Literature grounding:
#   Modgil & Prakken 2018, Def 19: Elitist/Democratic set comparison
#   requires commensurable vectors. Variable-length vectors make
#   cross-claim comparison meaningless (comparing log(sample_size)
#   against confidence is numerically incommensurable).


class TestClaimStrengthFixedLength:
    """Tests for fixed-length 3-element preference vectors.

    claim_strength() must always return a 3-element vector so that
    Def 19 (Modgil & Prakken 2018) set comparisons are commensurable
    across claims with different metadata profiles.
    """

    def test_claim_strength_fixed_length_all_fields(self):
        """Claim with all three metadata fields returns 3-element vector.

        All dimensions are populated from actual metadata — no defaults needed.
        """
        claim = {"sample_size": 100, "uncertainty": 0.2, "confidence": 0.9}
        result = claim_strength(claim)
        assert len(result) == 3

    def test_claim_strength_fixed_length_no_fields(self):
        """Claim with no metadata returns 3-element vector of neutral defaults.

        Neutral defaults: [0.0, 1.0, 0.5]
          - 0.0 for log_sample_size: log1p(0) = 0, weakest possible
          - 1.0 for inverse_uncertainty: 1/1.0, maximum uncertainty
          - 0.5 for confidence: coin flip, no advantage
        """
        result = claim_strength({})
        assert len(result) == 3
        assert result == [0.0, 1.0, 0.5]

    def test_claim_strength_fixed_length_partial(self):
        """Claim with only sample_size returns 3-element vector.

        Second element (inverse_uncertainty) and third element (confidence)
        must be neutral defaults.
        """
        result = claim_strength({"sample_size": 500})
        assert len(result) == 3
        # Second element: inverse_uncertainty default = 1.0
        assert result[1] == 1.0
        # Third element: confidence default = 0.5
        assert result[2] == 0.5

    def test_claim_strength_fixed_length_different_partials(self):
        """Claims with different metadata subsets return same-length vectors.

        Claim A has only sample_size; Claim B has only confidence.
        Both must return 3-element vectors for commensurable comparison
        under Def 19 (Modgil & Prakken 2018).
        """
        a = claim_strength({"sample_size": 100})
        b = claim_strength({"confidence": 0.8})
        assert len(a) == len(b) == 3

    def test_strictly_weaker_same_length_vectors(self):
        """Two claims with different metadata subsets produce same-length
        vectors for strictly_weaker() comparison.

        This verifies the precondition: vectors fed to strictly_weaker()
        from claim_strength() are always commensurable (same length),
        regardless of which metadata fields were present.
        """
        dims_a = claim_strength({"sample_size": 50})
        dims_b = claim_strength({"confidence": 0.7})
        # Both must be length 3 — the precondition for commensurable comparison
        assert len(dims_a) == 3
        assert len(dims_b) == 3
        # The comparison must be well-defined (no crash, meaningful result)
        result = strictly_weaker(dims_a, dims_b, "elitist")
        assert isinstance(result, bool)


class TestClaimStrengthFixedLengthProperties:
    """Hypothesis property tests for fixed-length preference vectors."""

    pytestmark = pytest.mark.property

    @given(st.fixed_dictionaries({}, optional={
        "sample_size": st.integers(min_value=1, max_value=100000),
        "uncertainty": st.floats(min_value=0.001, max_value=10.0, allow_nan=False),
        "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    }))
    @_PROP_SETTINGS
    def test_claim_strength_always_three_elements(self, claim):
        """P9: claim_strength() always returns exactly 3 elements.

        For any combination of present/absent metadata fields,
        the result must be a 3-element vector. This ensures Def 19
        (Modgil & Prakken 2018) set comparisons are commensurable.
        """
        result = claim_strength(claim)
        assert len(result) == 3

    @given(st.lists(
        st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=3, max_size=3,
    ), _comparisons)
    @_PROP_SETTINGS
    def test_strictly_weaker_irreflexive(self, v, mode):
        """P10: No 3-element strength vector is strictly weaker than itself.

        Irreflexivity — Modgil 2018 Def 19 implies this since
        "exists x < all y" (elitist) and "forall x exists y, x < y"
        (democratic) cannot hold when comparing identical sets, because
        x < x is always false for strict ordering.
        """
        assert strictly_weaker(v, v, mode) is False

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=1, max_size=5,
        ),
        st.lists(
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=1, max_size=5,
        ),
        _comparisons,
    )
    @_PROP_SETTINGS
    def test_defeat_holds_undercuts_always_true(self, a, b, mode):
        """P11: Undercutting always succeeds regardless of preferences.

        Modgil & Prakken 2018, Def 9: undercutting is preference-independent.
        No matter the strength vectors, undercuts always produces defeat.
        """
        assert defeat_holds("undercuts", a, b, mode) is True
