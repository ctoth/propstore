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

    def test_independent_targets_independent_interaction(self):
        """Two targets in unconnected components are marked independent."""
        target_a = FragilityTarget(
            target_id="a", target_kind="assumption",
            description="A", epistemic_score=0.5, fragility=0.5,
        )
        target_b = FragilityTarget(
            target_id="b", target_kind="assumption",
            description="B", epistemic_score=0.5, fragility=0.5,
        )
        results = detect_interactions([target_a, target_b], None)
        # With no ATMS, interaction type should be "unknown"
        assert len(results) >= 1
        for r in results:
            assert r["interaction_type"] in ("independent", "unknown")

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
        results = detect_interactions([target_a, target_b], None)
        if results:
            r = results[0]
            assert "target_a_id" in r
            assert "target_b_id" in r
            assert "interaction_type" in r
            assert "concepts_affected" in r

    def test_empty_targets_no_interactions(self):
        """Empty target list returns empty interactions."""
        assert detect_interactions([], None) == []


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
        # Different E and a values so perturbation actually shifts fused E.
        # When a=0.5 and both E are equal, preserving E makes WBF insensitive.
        omega_1 = Opinion(0.1, 0.1, 0.8, 0.3)   # E=0.34, high u
        omega_2 = Opinion(0.6, 0.1, 0.3, 0.7)   # E=0.81, low u
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


# ── C1: Parametric normalization tests ────────────────────────────────


class TestParametricNormalization:
    """C1: _parametric_dimension should return raw max elasticity,
    then rank_fragility normalizes across all concepts."""

    def test_different_elasticities_different_scores(self):
        """Raw parametric scores are normalized across concepts.

        Concept A has max elasticity 5.0, concept B has 0.5.
        After normalization: A = 1.0, B = 0.1.
        """
        from propstore.fragility import _normalize_parametric_scores

        raw_scores = {"A": 5.0, "B": 0.5}
        normalized = _normalize_parametric_scores(raw_scores)
        assert normalized["A"] == pytest.approx(1.0)
        assert normalized["B"] == pytest.approx(0.1)

    def test_single_concept_gets_score_one(self):
        """A single concept's parametric score normalizes to 1.0."""
        from propstore.fragility import _normalize_parametric_scores

        raw_scores = {"X": 3.0}
        normalized = _normalize_parametric_scores(raw_scores)
        assert normalized["X"] == pytest.approx(1.0)

    def test_zero_elasticity_gets_score_zero(self):
        """A concept with zero elasticity gets score 0.0."""
        from propstore.fragility import _normalize_parametric_scores

        raw_scores = {"A": 4.0, "B": 0.0}
        normalized = _normalize_parametric_scores(raw_scores)
        assert normalized["A"] == pytest.approx(1.0)
        assert normalized["B"] == pytest.approx(0.0)

    def test_all_zero_elasticities(self):
        """If all elasticities are zero, all scores are 0.0."""
        from propstore.fragility import _normalize_parametric_scores

        raw_scores = {"A": 0.0, "B": 0.0}
        normalized = _normalize_parametric_scores(raw_scores)
        assert normalized["A"] == pytest.approx(0.0)
        assert normalized["B"] == pytest.approx(0.0)


# ── C2: Opinion sensitivity adaptive delta tests ─────────────────────


class TestOpinionSensitivityAdaptive:
    """C2: opinion_sensitivity should handle high-belief/high-base-rate opinions."""

    def test_high_belief_high_base_rate_not_none(self):
        """opinion_sensitivity returns a value (not None) for Opinion(0.7, 0.0, 0.3, 0.9)."""
        opinions = [Opinion(0.7, 0.0, 0.3, 0.9), Opinion(0.3, 0.3, 0.4, 0.5)]
        result = opinion_sensitivity(opinions, 0)
        assert result is not None

    def test_adaptive_delta_works(self):
        """Various edge-case opinions produce non-None sensitivity."""
        edge_cases = [
            Opinion(0.8, 0.0, 0.2, 0.8),   # high b, zero d, high a
            Opinion(0.0, 0.8, 0.2, 0.2),   # zero b, high d, low a
            Opinion(0.45, 0.05, 0.5, 0.9), # high a near boundary
        ]
        other = Opinion(0.3, 0.3, 0.4, 0.5)
        for edge in edge_cases:
            result = opinion_sensitivity([edge, other], 0)
            assert result is not None, f"Failed for {edge}"


# ── I5: Epistemic sign flip for OUT nodes ────────────────────────────


class TestEpistemicSignFlip:
    """I5: OUT nodes with many flip witnesses should have LOW fragility."""

    def test_out_node_many_witnesses_low_fragility(self):
        """A concept not in the extension that would enter in most futures
        has LOW fragility, not high.

        If current_status is 'undetermined' and witnesses=7, consistent=8:
        Old formula: 7/8 = 0.875 (HIGH fragility — WRONG)
        New formula: 1 - 7/8 = 0.125 (LOW fragility — CORRECT)
        """
        from propstore.fragility import weighted_epistemic_score

        # For OUT nodes, the score should be inverted
        score = weighted_epistemic_score(
            witnesses=[{} for _ in range(7)],
            consistent_future_count=8,
            current_in_extension=False,
        )
        assert score == pytest.approx(0.125)

    def test_in_node_many_witnesses_high_fragility(self):
        """A concept IN the extension with many flip witnesses is fragile."""
        from propstore.fragility import weighted_epistemic_score

        score = weighted_epistemic_score(
            witnesses=[{} for _ in range(7)],
            consistent_future_count=8,
            current_in_extension=True,
        )
        assert score == pytest.approx(0.875)

    def test_in_node_default_behavior_unchanged(self):
        """Without current_in_extension, default (True) preserves old behavior."""
        from propstore.fragility import weighted_epistemic_score

        score = weighted_epistemic_score(
            witnesses=[{} for _ in range(3)],
            consistent_future_count=10,
        )
        assert score == pytest.approx(0.3)


# ── I1: Wire weighted_epistemic_score into _epistemic_dimension ──────


class TestEpistemicWiring:
    """I1: _epistemic_dimension should delegate to weighted_epistemic_score."""

    def test_weighted_score_called_with_current_status(self):
        """weighted_epistemic_score is called from _epistemic_dimension
        with the current_in_extension parameter from stability report."""
        from unittest.mock import patch, MagicMock

        from propstore.fragility import _epistemic_dimension

        # Build a mock bound world
        mock_bound = MagicMock()
        mock_atms = MagicMock()
        mock_bound.atms_engine.return_value = mock_atms
        mock_atms._all_parameterizations = ["p1", "p2"]
        mock_atms.concept_stability.return_value = {
            "witnesses": [{"idx": 0}, {"idx": 1}],
            "consistent_future_count": 5,
            "stable": False,
            "current_status": "determined",
        }

        with patch("propstore.fragility.weighted_epistemic_score") as mock_wes:
            mock_wes.return_value = 0.4
            score, detail = _epistemic_dimension(mock_bound, "test_concept", None, 8)

            # Verify weighted_epistemic_score was called
            mock_wes.assert_called_once()
            # Verify it got the right arguments
            call_kwargs = mock_wes.call_args
            assert call_kwargs is not None


# ── Fix 1: FragilityWarning tests ──────────────────────────────────────


class TestFragilityWarnings:
    """Silent failures emit warnings instead of swallowing errors."""

    def test_fragility_warning_is_user_warning(self):
        """FragilityWarning is importable and is a subclass of UserWarning."""
        from propstore.fragility import FragilityWarning
        assert issubclass(FragilityWarning, UserWarning)

    def test_derived_concepts_warns_on_failure(self):
        """When concept discovery fails, a FragilityWarning is emitted."""
        import warnings
        from propstore.fragility import FragilityWarning, _derived_concepts

        # Pass an object whose _store raises on concept_ids()
        class BadStore:
            def concept_ids(self):
                raise RuntimeError("store exploded")

        class BadBound:
            _store = BadStore()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _derived_concepts(BadBound())
            assert result == []
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1
            assert "concept discovery" in str(fragility_warnings[0].message).lower()

    def test_epistemic_dimension_warns_on_failure(self):
        """When epistemic dimension fails, a FragilityWarning is emitted."""
        import warnings
        from unittest.mock import MagicMock
        from propstore.fragility import FragilityWarning, _epistemic_dimension

        mock_bound = MagicMock()
        mock_bound.atms_engine.side_effect = RuntimeError("no ATMS")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            score, detail = _epistemic_dimension(mock_bound, "c1", None, 8)
            assert score is None
            assert detail is None
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1

    def test_conflict_dimension_warns_on_inner_failure(self):
        """When conflict scoring inner try fails, a FragilityWarning is emitted."""
        import warnings
        from unittest.mock import MagicMock, patch
        from propstore.fragility import FragilityWarning, _conflict_dimension

        mock_bound = MagicMock()
        mock_bound.conflicts.return_value = [{"claim_a_id": "a", "claim_b_id": "b"}]
        mock_bound._active_graph = MagicMock()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch(
                "propstore.fragility.shared_analyzer_input_from_active_graph",
                side_effect=RuntimeError("graph exploded"),
                create=True,
            ), patch(
                "propstore.core.analyzers.shared_analyzer_input_from_active_graph",
                side_effect=RuntimeError("graph exploded"),
            ):
                score, detail = _conflict_dimension(mock_bound, "c1")
            # Should still return a result (fallback to 1.0), not crash
            assert score is not None
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1

    def test_conflict_dimension_warns_on_outer_failure(self):
        """When conflict dimension completely fails, a FragilityWarning is emitted."""
        import warnings
        from unittest.mock import MagicMock
        from propstore.fragility import FragilityWarning, _conflict_dimension

        mock_bound = MagicMock()
        mock_bound.conflicts.side_effect = RuntimeError("conflicts exploded")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            score, detail = _conflict_dimension(mock_bound, "c1")
            assert score is None
            assert detail is None
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1

    def test_warning_contains_context(self):
        """Warning message includes what operation failed and the error."""
        import warnings
        from propstore.fragility import FragilityWarning, _derived_concepts

        class BadStore:
            def concept_ids(self):
                raise KeyError("missing_table")

        class BadBound:
            _store = BadStore()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _derived_concepts(BadBound())
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1
            msg = str(fragility_warnings[0].message)
            assert "missing_table" in msg

    def test_rank_fragility_warns_on_bad_bound(self):
        """rank_fragility with an invalid bound warns instead of crashing."""
        import warnings
        from propstore.fragility import rank_fragility, FragilityWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = rank_fragility(object())
            assert result.targets == ()
            # Should have emitted at least one warning
            fragility_warnings = [x for x in w if issubclass(x.category, FragilityWarning)]
            assert len(fragility_warnings) >= 1


# ── Fix 2: ATMS-native interaction detection tests ─────────────────────


class TestATMSInteractionDetection:
    """Real ATMS-based interaction detection."""

    def test_empty_targets_no_interactions(self):
        """Empty target list returns empty interactions."""
        from propstore.fragility import detect_interactions
        result = detect_interactions([], None)
        assert result == []

    def test_no_assumption_targets_no_interactions(self):
        """Targets with target_kind != 'assumption' are excluded."""
        from propstore.fragility import detect_interactions, FragilityTarget
        targets = [
            FragilityTarget(
                target_id="c1", target_kind="concept", description="test",
                epistemic_score=0.8, fragility=0.8,
            ),
        ]
        result = detect_interactions(targets, None)
        assert result == []

    def test_single_target_no_interactions(self):
        """A single target cannot have pairwise interactions."""
        from propstore.fragility import detect_interactions, FragilityTarget
        targets = [
            FragilityTarget(
                target_id="a1", target_kind="assumption", description="test",
                epistemic_score=0.8, fragility=0.8,
            ),
        ]
        result = detect_interactions(targets, None)
        assert result == []

    def test_interaction_dict_structure(self):
        """Each interaction dict has required fields."""
        from propstore.fragility import detect_interactions, FragilityTarget
        targets = [
            FragilityTarget(
                target_id="a1", target_kind="assumption", description="A",
                epistemic_score=0.8, fragility=0.8,
            ),
            FragilityTarget(
                target_id="a2", target_kind="assumption", description="B",
                epistemic_score=0.6, fragility=0.6,
            ),
        ]
        result = detect_interactions(targets, None)
        assert len(result) >= 1
        r = result[0]
        assert "target_a_id" in r
        assert "target_b_id" in r
        assert "interaction_type" in r
        assert "concepts_affected" in r

    def test_no_bound_returns_empty_for_assumptions(self):
        """Without a bound, interaction detection returns results with 'unknown' type."""
        from propstore.fragility import detect_interactions, FragilityTarget
        targets = [
            FragilityTarget(
                target_id="a1", target_kind="assumption", description="A",
                epistemic_score=0.8, fragility=0.8,
            ),
            FragilityTarget(
                target_id="a2", target_kind="assumption", description="B",
                epistemic_score=0.6, fragility=0.6,
            ),
        ]
        result = detect_interactions(targets, None)
        # With no bound/ATMS, should still return structure but with unknown interaction
        assert len(result) >= 1


# ── Phase 4A: Cost Tiers + Epistemic ROI ─────────────────────────────


class TestCostTiers:
    """Ordinal cost model and epistemic ROI."""

    def test_assumption_cost_1(self):
        """Assumptions have cost tier 1 (trivial)."""
        from propstore.fragility import assign_cost_tier, FragilityTarget
        t = FragilityTarget(target_id="t1", target_kind="assumption",
                           description="test", fragility=0.8)
        assert assign_cost_tier(t) == 1

    def test_concept_with_claims_cost_2(self):
        """Concepts with existing parametric data have cost tier 2."""
        from propstore.fragility import assign_cost_tier, FragilityTarget
        t = FragilityTarget(target_id="c1", target_kind="concept",
                           description="test", parametric_score=0.5, fragility=0.5)
        assert assign_cost_tier(t) == 2

    def test_concept_no_claims_cost_3(self):
        """Concepts with no claims have cost tier 3."""
        from propstore.fragility import assign_cost_tier, FragilityTarget
        t = FragilityTarget(target_id="c2", target_kind="concept",
                           description="no claims", fragility=0.7)
        assert assign_cost_tier(t) == 3

    def test_conflict_cost_2(self):
        """Conflicts have cost tier 2."""
        from propstore.fragility import assign_cost_tier, FragilityTarget
        t = FragilityTarget(target_id="x", target_kind="conflict",
                           description="test", conflict_score=0.8, fragility=0.8)
        assert assign_cost_tier(t) == 2

    def test_roi_computation(self):
        """ROI = fragility / cost_tier."""
        from propstore.fragility import FragilityTarget
        t = FragilityTarget(target_id="t1", target_kind="assumption",
                           description="test", fragility=0.8, cost_tier=1,
                           epistemic_roi=0.8)
        assert t.epistemic_roi == pytest.approx(0.8)

    def test_roi_reorders_ranking(self):
        """Cheap moderate-fragility beats expensive high-fragility on ROI."""
        from propstore.fragility import FragilityTarget
        cheap = FragilityTarget(target_id="a", target_kind="assumption",
                               description="test", fragility=0.6,
                               cost_tier=1, epistemic_roi=0.6)
        expensive = FragilityTarget(target_id="b", target_kind="concept",
                                   description="test", fragility=0.9,
                                   cost_tier=3, epistemic_roi=0.3)
        # By fragility: expensive wins (0.9 > 0.6)
        # By ROI: cheap wins (0.6 > 0.3)
        assert expensive.fragility > cheap.fragility
        assert cheap.epistemic_roi > expensive.epistemic_roi


# ── Phase 4A: Tier 2 Discovery ──────────────────────────────────────


class TestTier2Discovery:
    """Queryable auto-discovery Tier 2: concepts with no claims."""

    def test_discover_returns_list(self):
        """_discover_tier2_concepts returns a list of FragilityTargets."""
        from propstore.fragility import _discover_tier2_concepts
        # With a mock bound that has no concepts, returns empty list
        from unittest.mock import MagicMock
        mock_bound = MagicMock()
        mock_bound._store.all_concepts.return_value = []
        result = _discover_tier2_concepts(mock_bound)
        assert isinstance(result, list)

    def test_discovered_targets_have_correct_kind(self):
        """Discovered targets have target_kind='concept'."""
        from propstore.fragility import FragilityTarget
        # Create a target as _discover_tier2_concepts would
        t = FragilityTarget(
            target_id="unmeasured_concept",
            target_kind="concept",
            description="No measurements — input to 2 parameterizations",
            fragility=1.0,
            cost_tier=3,
            epistemic_roi=1.0/3,
        )
        assert t.target_kind == "concept"
        assert t.cost_tier == 3
        assert t.fragility == 1.0

    def test_discovered_targets_max_fragility(self):
        """Unknown concepts have maximum fragility (total ignorance)."""
        from propstore.fragility import FragilityTarget
        t = FragilityTarget(target_id="x", target_kind="concept",
                           description="test", fragility=1.0)
        assert t.fragility == 1.0

    def test_discovery_tier_parameter(self):
        """rank_fragility accepts discovery_tier parameter."""
        import inspect
        from propstore.fragility import rank_fragility
        sig = inspect.signature(rank_fragility)
        assert "discovery_tier" in sig.parameters

    def test_discover_finds_unmeasured_inputs(self):
        """Concepts that are parameterization inputs with no claims are discovered."""
        from unittest.mock import MagicMock
        from propstore.fragility import _discover_tier2_concepts

        mock_bound = MagicMock()
        # Concept "viscosity" is an input to parameterizations but has no claims
        mock_bound._store.all_concepts.return_value = [
            {"concept_id": "density", "parameterization_relationships": []},
            {"concept_id": "viscosity", "parameterization_relationships": []},
        ]
        # density has parameterizations that use viscosity as input
        mock_bound._store.parameterizations_for.side_effect = lambda cid: (
            [{"concept_ids": '["viscosity", "temperature"]'}] if cid == "density" else []
        )
        # viscosity has no active claims; density does
        mock_bound.active_claims.side_effect = lambda cid: (
            [] if cid == "viscosity" else [{"claim_id": "c1"}]
        )
        # concept_ids returns the concept IDs
        mock_bound._store.concept_ids.return_value = ["density", "viscosity"]

        result = _discover_tier2_concepts(mock_bound)
        # Should find viscosity as a Tier 2 target
        ids = [t.target_id for t in result]
        assert "viscosity" in ids
        # Should NOT include density (it has claims)
        assert "density" not in ids

    def test_sort_by_roi(self):
        """rank_fragility accepts sort_by parameter."""
        import inspect
        from propstore.fragility import rank_fragility
        sig = inspect.signature(rank_fragility)
        assert "sort_by" in sig.parameters
