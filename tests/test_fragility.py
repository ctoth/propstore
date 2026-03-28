"""Tests for propstore.fragility — epistemic fragility engine."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.fragility import (
    FragilityReport,
    FragilityTarget,
    combine_fragility,
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
