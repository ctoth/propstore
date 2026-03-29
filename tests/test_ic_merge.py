"""Tests for scalar IC-merge adaptation kernels and future integration points.

These tests cover the scalar-distance kernels inspired by Konieczny & Pino Perez
2002, their dispatcher, and RenderPolicy integration. They verify properties the
current scalar adaptation really has, not the full model-theoretic IC0-IC8
postulates from the paper.
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from propstore.repo.ic_merge import (
    MergeOperator,
    assignment_satisfies_mu,
    sigma_merge,
    max_merge,
    gmax_merge,
    ic_merge,
    claim_distance,
    scalar_profile_problem,
    solve_ic_merge,
)
from propstore.world.types import (
    ICMergeProblem,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeSource,
    RenderPolicy,
    ResolutionStrategy,
)

# ── Strategies ──────────────────────────────────────────────────────

# Strategy: numeric claim values in the current scalar adaptation
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

st_small_assignment_value = st.integers(min_value=0, max_value=2)

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


# ── Group 2: Sigma Operator (scalar sum-distance adaptation) ───────


class TestSigmaMerge:
    def test_sigma_unanimous(self):
        """When all branches agree, sigma returns the common value.

        In the scalar adaptation, unanimous profiles are fixed points.
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

        The scalar result depends on the multiset of values, not source labels.
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
    def test_sigma_result_closure(self, profile):
        """Sigma result is always one of the input values (closure over candidate set).

        This verifies discrete selection: the merge operator picks from the
        profile values, it does not interpolate.
        """
        assume(len(set(profile.values())) >= 2)  # at least two distinct values
        result = sigma_merge(profile)
        assert result in profile.values()


# ── Group 3: Max Operator (scalar max-distance adaptation) ─────────


class TestMaxMerge:
    def test_max_unanimous(self):
        """When all agree, max returns common value.

        In the scalar adaptation, unanimous profiles are fixed points.
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

        The scalar result depends on values, not source labels.
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

    def test_max_duplicate_invariance_exposes_scalar_limit(self):
        """Max ignores source multiplicity in the scalar adaptation.

        This is the arbitration-style property the current implementation really
        enforces. It should not be confused with the paper's full fairness
        postulates, which require a model-theoretic result space.
        """
        profile_majority = {"b1": 0.0, "b2": 0.0, "b3": 0.0, "b4": 10.0}
        result = max_merge(profile_majority)
        single_profile = {"b1": 0.0, "b2": 10.0}
        single_result = max_merge(single_profile)
        assert result == single_result

    def test_max_handles_unhashable_values(self):
        """Max must deduplicate equal unhashable values without crashing."""
        profile = {"b1": [1], "b2": [1], "b3": [2]}
        result = max_merge(profile)
        assert result == [1]


# ── Group 4: GMax Operator (scalar leximax adaptation) ─────────────


class TestGMaxMerge:
    def test_gmax_unanimous(self):
        """When all agree, gmax returns common value.

        In the scalar adaptation, unanimous profiles are fixed points.
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

        The scalar result depends on values, not source labels.
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

    def test_gmax_handles_unhashable_values(self):
        """GMax must deduplicate equal unhashable values without crashing."""
        profile = {
            "b1": {"value": 1},
            "b2": {"value": 1},
            "b3": {"value": 2},
        }
        result = gmax_merge(profile)
        assert result == {"value": 1}


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

        Sigma is the default aggregation kernel in the current scalar adapter.
        """
        profile = {"b1": 5.0, "b2": 10.0, "b3": 5.0}
        assert ic_merge(profile) == sigma_merge(profile)


class TestAssignmentLevelICMerge:
    def test_two_concept_problem_returns_assignment_winner(self):
        problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 1.0}),
                ),
                MergeSource(
                    source_id="s3",
                    assignment=MergeAssignment(values={"x": 1.0, "y": 1.0}),
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_ic_merge(problem)

        assert result.winners == (
            MergeAssignment(values={"x": 0.0, "y": 1.0}),
        )
        assert result.scored_candidates[0].assignment == MergeAssignment(
            values={"x": 0.0, "y": 1.0}
        )

    def test_problem_rejects_source_assignment_outside_declared_concepts(self):
        with pytest.raises(ValueError, match="unknown concept ids"):
            ICMergeProblem(
                concept_ids=("x", "y"),
                sources=(
                    MergeSource(
                        source_id="s1",
                        assignment=MergeAssignment(values={"x": 0.0, "z": 1.0}),
                    ),
                ),
                operator=MergeOperator.SIGMA,
            )

    def test_problem_rejects_duplicate_concept_ids(self):
        with pytest.raises(ValueError, match="duplicate concept ids"):
            ICMergeProblem(
                concept_ids=("x", "x"),
                sources=(
                    MergeSource(
                        source_id="s1",
                        assignment=MergeAssignment(values={"x": 0.0}),
                    ),
                ),
                operator=MergeOperator.SIGMA,
            )

    @given(
        st.lists(
            st.tuples(st_small_assignment_value, st_small_assignment_value),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        max_examples=40,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_multiconcept_source_order_does_not_change_winners(
        self,
        source_pairs,
        operator,
    ):
        forward_problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=tuple(
                MergeSource(
                    source_id=f"s{index}",
                    assignment=MergeAssignment(values={"x": x, "y": y}),
                )
                for index, (x, y) in enumerate(source_pairs)
            ),
            operator=operator,
        )
        reversed_problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=tuple(
                MergeSource(
                    source_id=f"r{index}",
                    assignment=MergeAssignment(values={"x": x, "y": y}),
                )
                for index, (x, y) in enumerate(reversed(source_pairs))
            ),
            operator=operator,
        )

        forward_result = solve_ic_merge(forward_problem)
        reversed_result = solve_ic_merge(reversed_problem)

        assert forward_result.winners == reversed_result.winners
        assert [
            (dict(item.assignment.values), item.score)
            for item in forward_result.scored_candidates
        ] == [
            (dict(item.assignment.values), item.score)
            for item in reversed_result.scored_candidates
        ]

    def test_range_constraint_filters_admissible_winners(self):
        profile = {"b1": 5.0, "b2": 10.0, "b3": 50.0}
        problem = scalar_profile_problem(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": 0.0, "upper": 20.0},
                ),
            ),
        )

        result = solve_ic_merge(problem)

        assert [winner.value_for("__value__") for winner in result.winners] == [10.0]
        assert result.admissible_count == 2

    def test_category_constraint_rejects_non_member_values(self):
        profile = {"b1": "speech", "b2": "whisper", "b3": "song"}
        problem = scalar_profile_problem(
            profile,
            operator=MergeOperator.MAX,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CATEGORY,
                    concept_ids=("__value__",),
                    metadata={
                        "allowed_values": ("speech", "whisper"),
                        "extensible": False,
                    },
                ),
            ),
        )

        result = solve_ic_merge(problem)

        assert all(
            winner.value_for("__value__") in {"speech", "whisper"}
            for winner in result.winners
        )
        assert result.admissible_count == 2

    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(
        max_examples=40,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_unconstrained_single_concept_matches_scalar_dispatch(self, profile, operator):
        problem = scalar_profile_problem(profile, operator=operator)

        result = solve_ic_merge(problem)

        assert result.scored_candidates
        assert result.scored_candidates[0].assignment.value_for("__value__") == ic_merge(
            profile,
            operator=operator,
        )

    @given(st_branch_profile)
    @settings(
        max_examples=40,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_winners_always_satisfy_range_mu(self, profile):
        ordered_values = sorted(profile.values())
        upper = ordered_values[len(ordered_values) // 2]
        problem = scalar_profile_problem(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": ordered_values[0], "upper": upper},
                ),
            ),
        )

        result = solve_ic_merge(problem)

        assert result.winners
        assert all(
            assignment_satisfies_mu(problem, winner)
            for winner in result.winners
        )

    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(
        max_examples=40,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_source_renaming_does_not_change_best_assignment(self, profile, operator):
        renamed = {
            f"renamed_{index}": value
            for index, value in enumerate(profile.values())
        }

        original_result = solve_ic_merge(scalar_profile_problem(profile, operator=operator))
        renamed_result = solve_ic_merge(scalar_profile_problem(renamed, operator=operator))

        assert original_result.scored_candidates
        assert renamed_result.scored_candidates
        assert (
            original_result.scored_candidates[0].assignment.value_for("__value__")
            == renamed_result.scored_candidates[0].assignment.value_for("__value__")
        )


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

    def test_render_policy_round_trips_merge_operator_enum(self):
        policy = RenderPolicy(merge_operator=MergeOperator.GMAX)

        restored = RenderPolicy.from_dict(policy.to_dict())

        assert restored.merge_operator == MergeOperator.GMAX
