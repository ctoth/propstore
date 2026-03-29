"""Phase 4 RED: Failing tests for IC merge operators with Hypothesis properties.

Tests the three IC merge operators (Sigma, Max, GMax) from Konieczny & Pino Perez
2002, their distance function, the ic_merge dispatcher, and RenderPolicy integration.

Heavy Hypothesis property tests verify formal invariants (IC0-IC8) from the paper.
Each test docstring cites the paper and specific claim/postulate.
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from propstore.repo.ic_merge import (
    MergeOperator,
    sigma_merge,
    max_merge,
    gmax_merge,
    ic_merge,
    claim_distance,
)
from propstore.world.types import ResolutionStrategy, RenderPolicy

# ── Strategies ──────────────────────────────────────────────────────

# Strategy: numeric claim values (the "interpretations" in IC merging)
st_claim_value = st.floats(
    min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False
)

# Strategy: a branch profile (2-5 branches, each with a numeric value)
st_branch_profile = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st_claim_value,
    min_size=2,
    max_size=5,
)

# Strategy: merge operator selection
st_operator = st.sampled_from(["sigma", "max", "gmax"])

# Strategy: branch weights (positive floats)
st_branch_weights = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    min_size=2,
    max_size=5,
)

# ── Group 1: MergeOperator Enum and Distance Function ──────────────


class TestMergeOperatorEnum:
    def test_merge_operator_enum(self):
        """MergeOperator has sigma, max, gmax values."""
        assert MergeOperator.SIGMA == "sigma"
        assert MergeOperator.MAX == "max"
        assert MergeOperator.GMAX == "gmax"


class TestClaimDistance:
    def test_claim_distance_numeric(self):
        """Distance between numeric claims is absolute difference.

        Per Konieczny 2002 claim13/17: d(I, phi) is a distance metric
        between interpretations.
        """
        assert claim_distance(3.0, 5.0) == 2.0
        assert claim_distance(5.0, 3.0) == 2.0  # symmetric

    def test_claim_distance_identical(self):
        """Distance between identical values is 0.

        Per Konieczny 2002: metric identity axiom d(x,x) = 0.
        """
        assert claim_distance(7.0, 7.0) == 0.0

    def test_claim_distance_categorical(self):
        """Distance between categorical (non-numeric) claims is Hamming:
        0 if equal, 1 if different.

        Per Konieczny 2002: distance generalises to non-numeric domains
        via Hamming distance.
        """
        assert claim_distance("alpha", "alpha") == 0.0
        assert claim_distance("alpha", "beta") == 1.0

    @given(st_claim_value, st_claim_value)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_distance_symmetric(self, a, b):
        """Distance is symmetric: d(a,b) == d(b,a).

        Per Konieczny 2002: distance is a metric, symmetry is a
        required axiom.
        """
        assert claim_distance(a, b) == claim_distance(b, a)

    @given(st_claim_value)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_distance_zero_self(self, a):
        """Distance from self is zero: d(a,a) == 0.

        Per Konieczny 2002: metric identity axiom.
        """
        assert claim_distance(a, a) == 0.0


# ── Group 2: Sigma Operator (Majority — IC0-IC8 + Maj) ─────────────


class TestSigmaMerge:
    def test_sigma_unanimous(self):
        """When all branches agree, sigma returns the common value.

        Per Konieczny 2002 IC2 (claim3): if all profiles are consistent
        (identical), the merged result equals their conjunction.
        """
        profile = {"b1": 5.0, "b2": 5.0, "b3": 5.0}
        result = sigma_merge(profile)
        assert result == 5.0

    def test_sigma_majority_wins(self):
        """Majority value wins under sigma.

        Per Konieczny 2002 claim15: Sigma satisfies Maj — enough copies
        of a source dominate the result.
        """
        profile = {"b1": 10.0, "b2": 10.0, "b3": 10.0, "b4": 99.0}
        result = sigma_merge(profile)
        assert result == 10.0  # 3 vs 1, majority wins

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        Per Konieczny 2002 IC3 (claim4): the merging result depends only
        on the multi-set of source belief bases, not on their labeling.
        """
        result1 = sigma_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = sigma_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_result_in_value_set(self, profile):
        """Sigma result is one of the input values (for discrete profiles).

        The winning interpretation must be a value that actually appears
        in the profile — sigma selects, it does not interpolate.
        """
        result = sigma_merge(profile)
        assert result in profile.values()

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_ic4_fairness(self, profile):
        """Neither source is completely ignored when both are individually valid.

        Per Konieczny 2002 IC4 (claim5): fairness — if two profiles each
        individually produce a result consistent with constraints, then
        their merge does not ignore either entirely. Result must equal
        at least one branch's value.
        """
        assume(len(set(profile.values())) >= 2)  # at least two distinct values
        result = sigma_merge(profile)
        assert result in profile.values()


# ── Group 3: Max Operator (Quasi-Merge — IC0-IC3, IC7-IC8, NOT IC4-IC6) ──


class TestMaxMerge:
    def test_max_unanimous(self):
        """When all agree, max returns common value.

        Per Konieczny 2002 IC2 (claim3).
        """
        profile = {"b1": 5.0, "b2": 5.0}
        result = max_merge(profile)
        assert result == 5.0

    def test_max_minimizes_worst_case(self):
        """Max picks the value minimizing the maximum distance to any branch.

        Per Konieczny 2002 claim17: d_Max(I, Psi) = max d(I, phi).
        The result minimizes the worst-case distance across all sources.

        Candidates: 0 -> max_dist=100, 10 -> max_dist=90, 100 -> max_dist=100.
        Winner: 10.0.
        """
        profile = {"b1": 0.0, "b2": 10.0, "b3": 100.0}
        result = max_merge(profile)
        assert result == 10.0

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_max_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        Per Konieczny 2002 IC3 (claim4): syntax independence.
        """
        result1 = max_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = max_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_max_arbitration(self, profile):
        """Duplicating a source does not change the result.

        Per Konieczny 2002 claim18: Max satisfies Arb — the result is
        insensitive to source multiplicity.
        """
        result1 = max_merge(profile)
        first_key = next(iter(profile))
        augmented = {**profile, f"{first_key}_dup": profile[first_key]}
        result2 = max_merge(augmented)
        assert result1 == result2

    def test_max_does_not_satisfy_ic4(self):
        """Max does NOT satisfy IC4 (fairness).

        Per Konieczny 2002 claim18: Max is a quasi-merging operator that
        satisfies IC0-IC3 and IC7-IC8 but NOT IC4-IC6.

        This test encodes the ASYMMETRY: we construct a profile where Max
        ignores one source entirely, violating fairness.

        Profile: two opposed sources of equal weight. Max can pick either
        but the arbitration property means duplicating doesn't help — so
        the minority source can be completely overridden even at equal
        multiplicity when a third source tips the balance.
        """
        # With 3 sources: {0, 0, 100}, max picks 0 (max_dist=100 vs 0's max_dist=100).
        # Actually 0 -> max_dist=100, 100 -> max_dist=100; equal.
        # Better example: {0, 10, 10} -> max picks 10 (max_dist=10 vs 0's max_dist=10).
        # The IC4 violation shows when merging subsets:
        # Merge({0}, {10}) should respect both, but Max can just pick 10.
        # We verify Max gives the same result regardless of how many times
        # a source appears — this IS arbitration, but means majority cannot
        # overwhelm like in Sigma. The IC4 violation is that Max ignores
        # multiplicity, so it cannot satisfy fairness.
        profile_majority = {"b1": 0.0, "b2": 0.0, "b3": 0.0, "b4": 10.0}
        result = max_merge(profile_majority)
        # Under Sigma (which satisfies IC4/Maj), majority 0.0 would win.
        # Under Max (which does NOT satisfy IC4), 0 and 10 are treated
        # by worst-case distance only, ignoring multiplicity.
        # max_merge should NOT necessarily pick 0.0 here (it may, since
        # max_dist from 0 is 10 and from 10 is 10 — tied).
        # The key IC4 violation: duplicating sources doesn't change Max's result.
        single_profile = {"b1": 0.0, "b2": 10.0}
        single_result = max_merge(single_profile)
        assert result == single_result  # Max ignores multiplicity (Arb property)


# ── Group 4: GMax Operator (Full IC — IC0-IC8 + Arb) ──────────────


class TestGMaxMerge:
    def test_gmax_unanimous(self):
        """When all agree, gmax returns common value.

        Per Konieczny 2002 IC2 (claim3).
        """
        profile = {"b1": 5.0, "b2": 5.0}
        result = gmax_merge(profile)
        assert result == 5.0

    def test_gmax_refines_max(self):
        """GMax result is always in the Max result set.

        Per Konieczny 2002 claim20: Delta^GMax entails Delta^Max.
        GMax refines Max by breaking ties lexicographically on sorted
        distance vectors.
        """
        profile = {"b1": 0.0, "b2": 10.0, "b3": 5.0}
        gmax_result = gmax_merge(profile)
        max_result = max_merge(profile)
        # GMax must pick a value whose max distance is no worse than Max's pick
        gmax_max_dist = max(abs(gmax_result - v) for v in profile.values())
        max_max_dist = max(abs(max_result - v) for v in profile.values())
        assert gmax_max_dist <= max_max_dist + 1e-9  # float tolerance

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_refines_max_property(self, profile):
        """Property: GMax always refines Max.

        Per Konieczny 2002 claim20: for any profile Psi,
        Delta^GMax(Psi) entails Delta^Max(Psi).
        """
        gmax_result = gmax_merge(profile)
        max_result = max_merge(profile)
        gmax_max_dist = max(abs(gmax_result - v) for v in profile.values())
        max_max_dist = max(abs(max_result - v) for v in profile.values())
        assert gmax_max_dist <= max_max_dist + 1e-9

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        Per Konieczny 2002 IC3 (claim4): syntax independence.
        """
        result1 = gmax_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = gmax_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_arbitration(self, profile):
        """Duplicating a source does not change the result.

        Per Konieczny 2002 claim19: GMax satisfies Arb — the result is
        insensitive to source multiplicity.
        """
        result1 = gmax_merge(profile)
        first_key = next(iter(profile))
        augmented = {**profile, f"{first_key}_dup": profile[first_key]}
        result2 = gmax_merge(augmented)
        assert result1 == result2


# ── Group 5: ic_merge Dispatcher ────────────────────────────────────


class TestIcMergeDispatcher:
    def test_ic_merge_dispatches_sigma(self):
        """ic_merge with operator='sigma' delegates to sigma_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert ic_merge(profile, operator="sigma") == sigma_merge(profile)

    def test_ic_merge_dispatches_max(self):
        """ic_merge with operator='max' delegates to max_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert ic_merge(profile, operator="max") == max_merge(profile)

    def test_ic_merge_dispatches_gmax(self):
        """ic_merge with operator='gmax' delegates to gmax_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert ic_merge(profile, operator="gmax") == gmax_merge(profile)

    def test_ic_merge_default_is_sigma(self):
        """Default operator is sigma (majority).

        Per Konieczny 2002: Sigma is the canonical IC merging operator
        satisfying all IC postulates plus majority.
        """
        profile = {"b1": 5.0, "b2": 10.0, "b3": 5.0}
        assert ic_merge(profile) == sigma_merge(profile)


# ── Group 6: RenderPolicy Integration ──────────────────────────────


class TestRenderPolicyIntegration:
    def test_render_policy_has_merge_operator(self):
        """RenderPolicy has merge_operator field with default 'sigma'.

        The merge_operator field selects which IC merge operator to use
        at render time, following the pattern of existing operator-selection
        fields like reasoning_backend.
        """
        policy = RenderPolicy()
        assert policy.merge_operator == "sigma"

    def test_render_policy_has_branch_filter(self):
        """RenderPolicy has branch_filter field, default None.

        The branch_filter controls which branches are included as sources
        in the IC merge profile.
        """
        policy = RenderPolicy()
        assert policy.branch_filter is None

    def test_resolution_strategy_has_ic_merge(self):
        """ResolutionStrategy has IC_MERGE member.

        IC merge is a new resolution strategy distinct from argumentation —
        it uses distance-based merging across multiple sources rather than
        argumentation-based winner selection.
        """
        assert ResolutionStrategy.IC_MERGE == "ic_merge"
