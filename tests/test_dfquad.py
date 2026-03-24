"""Tests for DF-QuAD gradual semantics.

Per Freedman et al. (2025, p.3): QBAFs extend Dung AFs with graded base
strengths tau(a) in [0,1] and explicit support relations R+, alongside
attack relations R-.
"""

from __future__ import annotations

import pytest

from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion
from propstore.praf import ProbabilisticAF, PrAFResult, compute_praf_acceptance
from propstore.praf_dfquad import (
    compute_dfquad_strengths,
    dfquad_aggregate,
    dfquad_combine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_praf(
    arguments: list[str],
    defeats: list[tuple[str, str]],
    base_scores: dict[str, float],
    attacks: list[tuple[str, str]] | None = None,
) -> ProbabilisticAF:
    """Build a ProbabilisticAF with Opinion-based base scores.

    Each argument gets Opinion.from_probability-like Opinion whose
    expectation() equals the requested base_score.  We use dogmatic
    opinions (b=score, d=1-score, u=0 is invalid for Opinion), so we
    use from_probability with high evidence count for near-deterministic.
    """
    from propstore.opinion import from_probability

    af = ArgumentationFramework(
        arguments=frozenset(arguments),
        defeats=frozenset(defeats),
        attacks=frozenset(attacks) if attacks is not None else None,
    )
    # Use from_probability with very high n so expectation() ≈ base_score
    p_args = {}
    for a in arguments:
        score = base_scores.get(a, 0.5)
        p_args[a] = from_probability(score, 10000)

    p_defeats = {}
    for d in defeats:
        # Defeat existence is certain
        p_defeats[d] = Opinion.dogmatic_true()

    return ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)


# ---------------------------------------------------------------------------
# Test 1: Isolated argument retains base score
# ---------------------------------------------------------------------------


class TestNoAttackersNoSupporters:
    """Per Freedman et al. (2025, p.3): isolated argument retains base score."""

    def test_isolated_argument_strength_equals_base_score(self) -> None:
        praf = _make_praf(["A"], [], {"A": 0.7})
        supports: dict[tuple[str, str], float] = {}
        strengths = compute_dfquad_strengths(praf, supports)
        assert strengths["A"] == pytest.approx(0.7, abs=0.01)

    def test_isolated_argument_base_half(self) -> None:
        praf = _make_praf(["A"], [], {"A": 0.5})
        strengths = compute_dfquad_strengths(praf, {})
        assert strengths["A"] == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# Test 2: Single attacker
# ---------------------------------------------------------------------------


class TestSingleAttacker:
    """A attacks B. B's strength < B's base_score. A's strength = A's base_score."""

    def test_target_strength_decreases(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.7})
        strengths = compute_dfquad_strengths(praf, {})
        assert strengths["B"] < 0.7
        assert strengths["A"] == pytest.approx(0.8, abs=0.01)

    def test_strong_attacker_reduces_more(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 1.0, "B": 0.7})
        strengths = compute_dfquad_strengths(praf, {})
        # With max-strength attacker, target should be driven toward 0
        assert strengths["B"] < 0.1


# ---------------------------------------------------------------------------
# Test 3: Single supporter
# ---------------------------------------------------------------------------


class TestSingleSupporter:
    """A supports B. B's strength > B's base_score. A's strength = A's base_score."""

    def test_target_strength_increases(self) -> None:
        praf = _make_praf(["A", "B"], [], {"A": 0.8, "B": 0.3})
        supports = {("A", "B"): 0.8}
        strengths = compute_dfquad_strengths(praf, supports)
        assert strengths["B"] > 0.3
        assert strengths["A"] == pytest.approx(0.8, abs=0.01)


# ---------------------------------------------------------------------------
# Test 4: Attacker monotonicity
# ---------------------------------------------------------------------------


class TestMonotonicityAttacker:
    """Per Freedman et al. (2025, Proposition 3): attacker monotonicity.

    Increasing attacker's base_score decreases target's strength.
    """

    def test_stronger_attacker_means_weaker_target(self) -> None:
        praf_weak = _make_praf(["A", "B"], [("A", "B")], {"A": 0.3, "B": 0.7})
        praf_strong = _make_praf(["A", "B"], [("A", "B")], {"A": 0.9, "B": 0.7})

        s_weak = compute_dfquad_strengths(praf_weak, {})
        s_strong = compute_dfquad_strengths(praf_strong, {})

        assert s_strong["B"] < s_weak["B"]


# ---------------------------------------------------------------------------
# Test 5: Supporter monotonicity
# ---------------------------------------------------------------------------


class TestMonotonicitySupporter:
    """Per Freedman et al. (2025, Proposition 3): supporter monotonicity.

    Increasing supporter's base_score increases target's strength.
    """

    def test_stronger_supporter_means_stronger_target(self) -> None:
        praf = _make_praf(["A", "B"], [], {"A": 0.3, "B": 0.5})
        supports = {("A", "B"): 0.3}
        s_weak = compute_dfquad_strengths(praf, supports)

        praf2 = _make_praf(["A", "B"], [], {"A": 0.9, "B": 0.5})
        supports2 = {("A", "B"): 0.9}
        s_strong = compute_dfquad_strengths(praf2, supports2)

        assert s_strong["B"] > s_weak["B"]


# ---------------------------------------------------------------------------
# Test 6: Contestability
# ---------------------------------------------------------------------------


class TestContestability:
    """Per Freedman et al. (2025, Proposition 4): argument relation contestability.

    Moving an argument from support to attack decreases target's strength.
    """

    def test_support_to_attack_decreases_strength(self) -> None:
        # A supports B
        praf_support = _make_praf(["A", "B"], [], {"A": 0.8, "B": 0.5})
        supports_only = {("A", "B"): 0.8}
        s_support = compute_dfquad_strengths(praf_support, supports_only)

        # A attacks B
        praf_attack = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.5})
        s_attack = compute_dfquad_strengths(praf_attack, {})

        assert s_attack["B"] < s_support["B"]


# ---------------------------------------------------------------------------
# Test 7: Boundedness
# ---------------------------------------------------------------------------


class TestBoundedness:
    """All outputs in [0,1] for all inputs in [0,1]."""

    @pytest.mark.parametrize(
        "base_a,base_b",
        [
            (0.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0),
            (1.0, 0.0),
            (0.5, 0.5),
        ],
    )
    def test_attack_bounded(self, base_a: float, base_b: float) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": base_a, "B": base_b})
        strengths = compute_dfquad_strengths(praf, {})
        for s in strengths.values():
            assert 0.0 <= s <= 1.0

    def test_many_attackers_bounded(self) -> None:
        args = ["T"] + [f"A{i}" for i in range(5)]
        defeats = [(f"A{i}", "T") for i in range(5)]
        scores = {"T": 0.9}
        for i in range(5):
            scores[f"A{i}"] = 0.9
        praf = _make_praf(args, defeats, scores)
        strengths = compute_dfquad_strengths(praf, {})
        for s in strengths.values():
            assert 0.0 <= s <= 1.0

    def test_many_supporters_bounded(self) -> None:
        args = ["T"] + [f"S{i}" for i in range(5)]
        scores = {"T": 0.1}
        supports: dict[tuple[str, str], float] = {}
        for i in range(5):
            scores[f"S{i}"] = 0.9
            supports[(f"S{i}", "T")] = 0.9
        praf = _make_praf(args, [], scores)
        strengths = compute_dfquad_strengths(praf, supports)
        for s in strengths.values():
            assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# Test 8: Chain propagation
# ---------------------------------------------------------------------------


class TestChainPropagation:
    """A supports B, B attacks C. Multi-hop propagation.

    A's high score should increase B's score, which should decrease C's score.
    """

    def test_support_then_attack_chain(self) -> None:
        praf = _make_praf(
            ["A", "B", "C"], [("B", "C")], {"A": 0.9, "B": 0.5, "C": 0.7}
        )
        supports = {("A", "B"): 0.9}
        strengths = compute_dfquad_strengths(praf, supports)

        # B should be strengthened by A's support
        assert strengths["B"] > 0.5
        # C should be weakened because B (now stronger) attacks it
        assert strengths["C"] < 0.7


# ---------------------------------------------------------------------------
# Test 9: PrAF dispatch
# ---------------------------------------------------------------------------


class TestPrAFDispatch:
    """compute_praf_acceptance(praf, strategy='dfquad') returns PrAFResult."""

    def test_dfquad_strategy_returns_result(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.6})
        result = compute_praf_acceptance(praf, strategy="dfquad")
        assert isinstance(result, PrAFResult)
        assert result.strategy_used == "dfquad"
        assert result.samples is None
        assert result.confidence_interval_half is None
        assert "A" in result.acceptance_probs
        assert "B" in result.acceptance_probs


# ---------------------------------------------------------------------------
# Test 10: DF-QuAD vs deterministic for extreme case
# ---------------------------------------------------------------------------


class TestDFQuADVsDeterministic:
    """For A attacks B with base_score=1.0 for A, DF-QuAD should give
    A strength=1.0 and B strength=0.0 — matching grounded extension.
    """

    def test_deterministic_extreme(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 1.0, "B": 1.0})
        strengths = compute_dfquad_strengths(praf, {})
        # A has no attackers, base=1.0 → strength=1.0
        assert strengths["A"] == pytest.approx(1.0, abs=0.01)
        # B attacked by A (strength 1.0), combined_influence = -1.0
        # f_agg(1.0, -1.0) = 1.0 + (-1.0)*1.0 = 0.0
        assert strengths["B"] == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# Unit tests for aggregation/combine functions
# ---------------------------------------------------------------------------


class TestDFQuADAggregateFunction:
    """Unit tests for the aggregation function itself."""

    def test_positive_influence(self) -> None:
        # f_agg(0.5, 0.5) = 0.5 + 0.5*(1-0.5) = 0.75
        assert dfquad_aggregate(0.5, 0.5) == pytest.approx(0.75)

    def test_negative_influence(self) -> None:
        # f_agg(0.5, -0.5) = 0.5 + (-0.5)*0.5 = 0.25
        assert dfquad_aggregate(0.5, -0.5) == pytest.approx(0.25)

    def test_zero_influence(self) -> None:
        assert dfquad_aggregate(0.7, 0.0) == pytest.approx(0.7)

    def test_max_positive(self) -> None:
        # f_agg(0.3, 1.0) = 0.3 + 1.0*(1-0.3) = 1.0
        assert dfquad_aggregate(0.3, 1.0) == pytest.approx(1.0)

    def test_max_negative(self) -> None:
        # f_agg(0.3, -1.0) = 0.3 + (-1.0)*0.3 = 0.0
        assert dfquad_aggregate(0.3, -1.0) == pytest.approx(0.0)


class TestDFQuADCombineFunction:
    """Unit tests for the combine function."""

    def test_no_supporters_no_attackers(self) -> None:
        assert dfquad_combine([], []) == pytest.approx(0.0)

    def test_one_supporter(self) -> None:
        # support = 1 - (1-0.8) = 0.8, attack = 0, combined = 0.8
        assert dfquad_combine([0.8], []) == pytest.approx(0.8)

    def test_one_attacker(self) -> None:
        # support = 0, attack = 1 - (1-0.8) = 0.8, combined = -0.8
        assert dfquad_combine([], [0.8]) == pytest.approx(-0.8)

    def test_equal_support_and_attack(self) -> None:
        # Both 0.5: support = 0.5, attack = 0.5, combined = 0.0
        assert dfquad_combine([0.5], [0.5]) == pytest.approx(0.0)

    def test_multiple_supporters(self) -> None:
        # support = 1 - (1-0.5)*(1-0.5) = 1 - 0.25 = 0.75
        assert dfquad_combine([0.5, 0.5], []) == pytest.approx(0.75)

    def test_multiple_attackers(self) -> None:
        # attack = 1 - (1-0.5)*(1-0.5) = 0.75, combined = -0.75
        assert dfquad_combine([], [0.5, 0.5]) == pytest.approx(-0.75)
