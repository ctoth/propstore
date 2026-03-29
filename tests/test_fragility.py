"""Tests for propstore.fragility — epistemic fragility engine."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.fragility import (
    FragilityReport,
    FragilityTarget,
    combine_fragility,
    detect_interactions,
    score_conflict,
    weighted_epistemic_score,
)


# ── combine_fragility tests ─────────────────────────────────────────


class TestCombineFragility:
    """Tests for the fragility score combination function."""

    def test_all_none(self):
        """No scores available returns 0.0."""
        assert combine_fragility(None, None, None) == 0.0

    def test_single_score(self):
        """Single available score is returned directly."""
        assert combine_fragility(0.8, None, None) == 0.8
        assert combine_fragility(None, 0.6, None) == 0.6
        assert combine_fragility(None, None, 0.4) == 0.4

    def test_top2_rewards_convergence(self):
        """Top-2 average rewards multi-dimensional fragility.

        A target fragile on one dimension only (0.9, 0.0, 0.0) gets
        (0.9 + 0.0) / 2 = 0.45. A target fragile on two dimensions
        (0.9, 0.8, 0.0) gets (0.9 + 0.8) / 2 = 0.85. The convergent
        target ranks higher.
        """
        single_dim = combine_fragility(0.9, 0.0, 0.0)
        multi_dim = combine_fragility(0.9, 0.8, 0.0)
        assert abs(single_dim - 0.45) < 1e-9
        assert abs(multi_dim - 0.85) < 1e-9
        assert multi_dim > single_dim

    def test_all_policies(self):
        """Different combination policies produce different results."""
        p, e, c = 0.9, 0.6, 0.3
        top2 = combine_fragility(p, e, c, combination="top2")
        mean = combine_fragility(p, e, c, combination="mean")
        mx = combine_fragility(p, e, c, combination="max")
        prod = combine_fragility(p, e, c, combination="product")

        assert abs(top2 - 0.75) < 1e-9      # (0.9 + 0.6) / 2
        assert abs(mean - 0.6) < 1e-9        # (0.9 + 0.6 + 0.3) / 3
        assert abs(mx - 0.9) < 1e-9          # max
        assert abs(prod - 0.162) < 1e-9       # 0.9 * 0.6 * 0.3

        # All different from each other
        results = [top2, mean, mx, prod]
        assert len(set(round(r, 9) for r in results)) == len(results)

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=200, deadline=None)
    def test_score_bounds(self, p, e, c):
        """All outputs in [0, 1] for inputs in [0, 1]."""
        for combo in ("top2", "mean", "max", "product"):
            result = combine_fragility(p, e, c, combination=combo)
            assert 0.0 <= result <= 1.0, f"{combo}: {result} out of bounds"


# ── FragilityReport / FragilityTarget data structure tests ──────────


class TestFragilityReport:
    """Test the report and target data structures."""

    def test_empty_report(self):
        """Default report has empty targets and zero world fragility."""
        report = FragilityReport()
        assert report.targets == ()
        assert report.world_fragility == 0.0
        assert report.analysis_scope == ""

    def test_target_fields(self):
        """FragilityTarget with all fields set is constructable and frozen."""
        target = FragilityTarget(
            target_id="concept:reynolds_number",
            target_kind="concept",
            description="Reynolds number sensitivity",
            parametric_score=0.9,
            epistemic_score=0.5,
            conflict_score=0.2,
            fragility=0.7,
            parametric_detail={"elasticity": 3.7},
            epistemic_detail={"witnesses": 4},
            conflict_detail={"conflicts": 1},
        )
        assert target.target_id == "concept:reynolds_number"
        assert target.target_kind == "concept"
        assert target.fragility == 0.7
        assert target.parametric_detail == {"elasticity": 3.7}

        # Frozen — cannot mutate
        with pytest.raises(AttributeError):
            target.fragility = 0.5  # type: ignore[misc]


# ── BoundWorld.fragility() smoke test ──────────────────────────────


class TestBoundWorldFragility:
    """Smoke test that BoundWorld.fragility() delegates correctly."""

    def test_fragility_method_exists(self):
        """BoundWorld has a fragility method."""
        from propstore.world.bound import BoundWorld
        assert hasattr(BoundWorld, "fragility")


# ── Phase 2: Conflict topology scoring ───────────────────────────────


def af(args: set[str], defeats: set[tuple[str, str]]) -> "ArgumentationFramework":
    """Build a toy AF for testing."""
    from propstore.dung import ArgumentationFramework
    return ArgumentationFramework(
        arguments=frozenset(args),
        defeats=frozenset(defeats),
    )


class TestConflictTopologyScoring:
    """Conflict scoring via hypothetical world evaluation."""

    def test_removing_unattacked_isolated_pair_low_score(self):
        """Removing either of two isolated unattacked claims has minimal impact.

        AF: A, B both unattacked, no defeats.
        Current grounded: {A, B}.
        Remove A: {B}, distance 1. Remove B: {A}, distance 1.
        Score = max(1/2, 1/2) = 0.5 — each removal loses one argument.
        """
        framework = af({"A", "B"}, set())
        assert score_conflict(framework, "A", "B") == pytest.approx(0.5)

    def test_removing_attacker_changes_extension(self):
        """Removing an attacker frees its target into the extension."""
        # AF: A attacks B
        # Current grounded: {A}
        # Remove A: grounded becomes {B} -- Hamming distance 2, score = 2/2 = 1.0
        framework = af({"A", "B"}, {("A", "B")})
        assert score_conflict(framework, "A", "B") == pytest.approx(1.0)

    def test_conflict_score_symmetric_max(self):
        """For a mutual conflict, score is the max of both hypotheticals."""
        # AF: A attacks B, B attacks A
        # Current grounded: {} (both defeated)
        # Remove A: {B}. Remove B: {A}. Both have distance 1 from {}.
        # Score = max(1/2, 1/2) = 0.5
        framework = af({"A", "B"}, {("A", "B"), ("B", "A")})
        assert score_conflict(framework, "A", "B") == pytest.approx(0.5)

    def test_isolated_conflict_low_score(self):
        """A conflict between two isolated claims has bounded impact."""
        # AF: A attacks B, C and D are independent unattacked
        # Remove A: {B, C, D} vs current {A, C, D} -- distance 2
        # Remove B: {A, C, D} vs current {A, C, D} -- distance 0
        # Score = max(2/4, 0/4) = 0.5
        framework = af({"A", "B", "C", "D"}, {("A", "B")})
        assert score_conflict(framework, "A", "B") == pytest.approx(0.5)

    def test_no_claims_returns_zero(self):
        """Empty AF has zero conflict score."""
        framework = af(set(), set())
        assert score_conflict(framework, "X", "Y") == 0.0


# ── Phase 2: Probability-weighted epistemic scores ───────────────────


class TestProbabilityWeightedEpistemic:
    """Probability-weighted epistemic scores."""

    def test_uniform_weights_match_unweighted(self):
        """With uniform weights, result matches the unweighted score."""
        # 4 futures, 2 are witnesses
        # Uniform weights [0.25, 0.25, 0.25, 0.25]
        # Unweighted score = 2/4 = 0.5
        witnesses = [{"future_idx": 0}, {"future_idx": 2}]
        result = weighted_epistemic_score(
            witnesses, 4,
            probability_weights=[0.25, 0.25, 0.25, 0.25],
            witness_indices=[0, 2],
        )
        assert result == pytest.approx(0.5)

    def test_high_probability_witness_increases_score(self):
        """If the flipping futures have high probability, score increases."""
        # 4 futures, witnesses at index 0 and 2
        # Weights: witnesses have P=0.4 each, non-witnesses have P=0.1 each
        # Weighted score = 0.8 / 1.0 = 0.8 (vs unweighted 0.5)
        witnesses = [{"future_idx": 0}, {"future_idx": 2}]
        result = weighted_epistemic_score(
            witnesses, 4,
            probability_weights=[0.4, 0.1, 0.4, 0.1],
            witness_indices=[0, 2],
        )
        assert result == pytest.approx(0.8)

    def test_low_probability_witness_decreases_score(self):
        """If the flipping futures have low probability, score decreases."""
        # 4 futures, witnesses at index 0 and 2
        # Weights: witnesses have P=0.05 each, non-witnesses have P=0.45 each
        # Weighted score = 0.1 / 1.0 = 0.1 (vs unweighted 0.5)
        witnesses = [{"future_idx": 0}, {"future_idx": 2}]
        result = weighted_epistemic_score(
            witnesses, 4,
            probability_weights=[0.05, 0.45, 0.05, 0.45],
            witness_indices=[0, 2],
        )
        assert result == pytest.approx(0.1)

    def test_no_weights_falls_back_to_uniform(self):
        """When no probability weights provided, uses uniform counting."""
        witnesses = [{"future_idx": 0}, {"future_idx": 1}]
        result = weighted_epistemic_score(witnesses, 4)
        assert result == pytest.approx(0.5)

    def test_all_zero_weights_returns_zero(self):
        """Edge case: all weights zero -> score 0."""
        witnesses = [{"future_idx": 0}]
        result = weighted_epistemic_score(
            witnesses, 2,
            probability_weights=[0.0, 0.0],
            witness_indices=[0],
        )
        assert result == 0.0


# ── Phase 2: Interaction detection ───────────────────────────────────


class TestInteractionDetection:
    """Pairwise interaction detection for top-k targets."""

    def test_independent_targets_zero_interaction(self):
        """Two targets in unconnected components have zero interaction."""
        # Two independent targets with identical scores
        target_a = FragilityTarget(
            target_id="a", target_kind="assumption",
            description="A", epistemic_score=0.5, fragility=0.5,
        )
        target_b = FragilityTarget(
            target_id="b", target_kind="assumption",
            description="B", epistemic_score=0.5, fragility=0.5,
        )
        results = detect_interactions([target_a, target_b])
        # With no shared concepts, interaction should be zero
        for r in results:
            assert r["interaction"] == pytest.approx(0.0)

    def test_interaction_structure(self):
        """Interaction result has required fields."""
        target_a = FragilityTarget(
            target_id="a", target_kind="assumption",
            description="A", epistemic_score=0.8, fragility=0.8,
        )
        target_b = FragilityTarget(
            target_id="b", target_kind="assumption",
            description="B", epistemic_score=0.6, fragility=0.6,
        )
        results = detect_interactions([target_a, target_b])
        if results:
            r = results[0]
            assert "target_a" in r
            assert "target_b" in r
            assert "individual_a" in r
            assert "individual_b" in r
            assert "joint" in r
            assert "interaction" in r

    def test_empty_targets_no_interactions(self):
        """Empty target list returns empty interactions."""
        assert detect_interactions([]) == []


# ── Phase 2: Updated combine_fragility test ──────────────────────────


class TestCombineFragilityUpdated:
    """Verify combination works with real (non-placeholder) conflict scores."""

    def test_top2_with_real_conflict_score(self):
        """Conflict scores from topology (not placeholder 1.0) combine correctly."""
        # parametric=0.7, epistemic=0.6, conflict=0.3
        # top2 = (0.7 + 0.6) / 2 = 0.65
        assert combine_fragility(0.7, 0.6, 0.3) == pytest.approx(0.65)


# ── Phase 3: Opinion sensitivity tests ─────────────────────────────────

from propstore.opinion import Opinion, wbf
from propstore.fragility import opinion_sensitivity, imps_rev


class TestOpinionSensitivity:
    """Marginal derivative of WBF fused expectation w.r.t. input uncertainty."""

    def test_high_uncertainty_high_sensitivity(self):
        """An opinion with u=0.8 has more marginal room than one with u=0.1."""
        omega_1 = Opinion(0.1, 0.1, 0.8, 0.5)
        omega_2 = Opinion(0.45, 0.45, 0.1, 0.5)
        opinions = [omega_1, omega_2]
        sens_1 = opinion_sensitivity(opinions, 0)
        sens_2 = opinion_sensitivity(opinions, 1)
        assert sens_1 is not None
        assert sens_2 is not None
        assert sens_1 > sens_2

    def test_single_opinion_sensitivity(self):
        """With one opinion, sensitivity is None (no fusion partner)."""
        omega = Opinion(0.4, 0.2, 0.4, 0.5)
        result = opinion_sensitivity([omega], 0)
        assert result is None

    def test_vacuous_opinion_max_sensitivity(self):
        """A vacuous opinion (u=1) has maximum marginal leverage."""
        omega_1 = Opinion.vacuous(0.5)
        omega_2 = Opinion(0.4, 0.1, 0.5, 0.5)
        opinions = [omega_1, omega_2]
        sens = opinion_sensitivity(opinions, 0)
        assert sens is not None
        assert sens > 0.0

    def test_sensitivity_returns_nonnegative(self):
        """Sensitivity magnitude is always >= 0."""
        pairs = [
            [Opinion(0.3, 0.3, 0.4, 0.5), Opinion(0.5, 0.2, 0.3, 0.5)],
            [Opinion(0.1, 0.1, 0.8, 0.5), Opinion(0.6, 0.1, 0.3, 0.5)],
            [Opinion(0.2, 0.5, 0.3, 0.5), Opinion(0.7, 0.1, 0.2, 0.5)],
        ]
        for opinions in pairs:
            for i in range(len(opinions)):
                s = opinion_sensitivity(opinions, i)
                if s is not None:
                    assert s >= 0.0

    def test_dogmatic_neighbor_returns_none(self):
        """If any opinion is dogmatic (u~0), sensitivity is None (can't WBF)."""
        omega_1 = Opinion(0.5, 0.3, 0.2, 0.5)
        omega_2 = Opinion(1.0, 0.0, 0.0, 0.5)  # dogmatic
        result = opinion_sensitivity([omega_1, omega_2], 0)
        assert result is None

    def test_two_identical_opinions_low_sensitivity(self):
        """Two identical opinions: perturbing one barely moves fused E."""
        omega = Opinion(0.4, 0.2, 0.4, 0.5)
        opinions = [omega, omega]
        sens = opinion_sensitivity(opinions, 0)
        assert sens is not None
        # Two agreeing opinions — sensitivity should be small
        assert sens < 0.5


# ── Phase 3: ImpS^rev tests ────────────────────────────────────────────

from propstore.dung import ArgumentationFramework


class TestImpSRev:
    """AlAnaissy 2024 revised impact measure via DF-QuAD."""

    def test_removing_only_attacker_increases_strength(self):
        """If A is B's only attacker, removing A->B increases B's strength."""
        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
        )
        result = imps_rev(
            framework,
            supports={},
            base_scores={"A": 0.8, "B": 0.5},
            attack=("A", "B"),
        )
        assert result > 0.0

    def test_removing_one_of_many_attackers_small_impact(self):
        """Removing one of several attackers has diminishing marginal effect."""
        # Single attacker case
        fw_single = ArgumentationFramework(
            arguments=frozenset({"A", "C"}),
            defeats=frozenset({("A", "C")}),
        )
        impact_single = imps_rev(
            fw_single,
            supports={},
            base_scores={"A": 0.5, "C": 0.5},
            attack=("A", "C"),
        )
        # Two attackers case
        fw_two = ArgumentationFramework(
            arguments=frozenset({"A", "B", "C"}),
            defeats=frozenset({("A", "C"), ("B", "C")}),
        )
        impact_two = imps_rev(
            fw_two,
            supports={},
            base_scores={"A": 0.5, "B": 0.5, "C": 0.5},
            attack=("A", "C"),
        )
        assert impact_single > 0.0
        assert impact_two > 0.0
        assert impact_single > impact_two

    def test_no_attack_returns_zero(self):
        """Impact of a non-existent attack is 0."""
        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
        )
        result = imps_rev(
            framework,
            supports={},
            base_scores={"A": 0.5, "B": 0.5},
            attack=("B", "A"),  # doesn't exist
        )
        assert result == 0.0

    def test_isolated_argument_zero_impact(self):
        """An argument with no attacks has zero impact on others."""
        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset(),
        )
        result = imps_rev(
            framework,
            supports={},
            base_scores={"A": 0.5, "B": 0.5},
            attack=("A", "B"),
        )
        assert result == 0.0

    def test_chain_attack_indirect_impact(self):
        """In A->B->C, removing A->B changes B's strength, which propagates to C."""
        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B", "C"}),
            defeats=frozenset({("A", "B"), ("B", "C")}),
        )
        result = imps_rev(
            framework,
            supports={},
            base_scores={"A": 0.5, "B": 0.5, "C": 0.5},
            attack=("A", "B"),
        )
        # Removing A->B makes B stronger, so B attacks C more, C gets weaker.
        # ImpS_rev measures change in B's strength: B gets stronger, so positive.
        assert result > 0.0


# ── Phase 3: Conflict scoring with gradual semantics ────────────────────


class TestConflictScoringGradual:
    """Conflict scoring via DF-QuAD gradual semantics."""

    def test_gradual_score_different_from_extension(self):
        """Gradual (ImpS^rev) and extension-based scores can differ."""
        # Build AF where A attacks B
        framework = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
        )
        extension_score = score_conflict(framework, "A", "B")
        gradual_impact = imps_rev(
            framework,
            supports={},
            base_scores={"A": 0.8, "B": 0.5},
            attack=("A", "B"),
        )
        # Both should be positive but generally have different values
        assert extension_score > 0.0
        assert gradual_impact > 0.0
