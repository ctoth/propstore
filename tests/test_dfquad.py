"""Tests for DF-QuAD gradual semantics.

Per Freedman et al. (2025, p.3): QBAFs extend Dung AFs with graded base
strengths tau(a) in [0,1] and explicit support relations R+, alongside
attack relations R-.
"""

from __future__ import annotations

import pytest

from argumentation.dung import ArgumentationFramework
from argumentation.dfquad import (
    dfquad_aggregate,
    dfquad_bipolar_strengths,
    dfquad_combine,
    dfquad_strengths,
)
from argumentation.gradual import WeightedBipolarGraph
from argumentation.probabilistic import (
    PrAFResult,
    ProbabilisticAF,
    compute_probabilistic_acceptance,
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
    """Build a pure ProbabilisticAF with float base scores."""
    af = ArgumentationFramework(
        arguments=frozenset(arguments),
        defeats=frozenset(defeats),
        attacks=frozenset(attacks) if attacks is not None else None,
    )
    p_args = {a: base_scores.get(a, 0.5) for a in arguments}
    p_defeats = {d: 1.0 for d in defeats}

    return ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)


def _tau_from_praf(praf: ProbabilisticAF) -> dict[str, float]:
    return {
        arg: praf.p_args[arg]
        for arg in praf.framework.arguments
    }


def _compute_quad_strengths(
    praf: ProbabilisticAF,
    supports: dict[tuple[str, str], float],
) -> dict[str, float]:
    return compute_dfquad_quad_strengths(
        praf,
        supports,
        tau=_tau_from_praf(praf),
    )


def compute_dfquad_quad_strengths(
    praf: ProbabilisticAF,
    supports: dict[tuple[str, str], float],
    *,
    tau: dict[str, float],
) -> dict[str, float]:
    graph = WeightedBipolarGraph(
        arguments=praf.framework.arguments,
        initial_weights=tau,
        attacks=praf.framework.defeats,
        supports=frozenset(supports),
    )
    return dfquad_strengths(
        graph,
        base_scores=tau,
        support_weights=supports,
    ).strengths


def compute_dfquad_baf_strengths(
    praf: ProbabilisticAF,
    supports: dict[tuple[str, str], float],
) -> dict[str, float]:
    graph = WeightedBipolarGraph(
        arguments=praf.framework.arguments,
        initial_weights={argument: 0.5 for argument in praf.framework.arguments},
        attacks=praf.framework.defeats,
        supports=frozenset(supports),
    )
    return dfquad_bipolar_strengths(graph).strengths


# ---------------------------------------------------------------------------
# Test 1: Isolated argument retains base score
# ---------------------------------------------------------------------------


class TestNoAttackersNoSupporters:
    """Per Freedman et al. (2025, p.3): isolated argument retains base score."""

    def test_isolated_argument_strength_equals_base_score(self) -> None:
        praf = _make_praf(["A"], [], {"A": 0.7})
        supports: dict[tuple[str, str], float] = {}
        strengths = _compute_quad_strengths(praf, supports)
        assert strengths["A"] == pytest.approx(0.7, abs=0.01)

    def test_isolated_argument_base_half(self) -> None:
        praf = _make_praf(["A"], [], {"A": 0.5})
        strengths = _compute_quad_strengths(praf, {})
        assert strengths["A"] == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# Test 2: Single attacker
# ---------------------------------------------------------------------------


class TestSingleAttacker:
    """A attacks B. B's strength < B's base_score. A's strength = A's base_score."""

    def test_target_strength_decreases(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.7})
        strengths = _compute_quad_strengths(praf, {})
        assert strengths["B"] < 0.7
        assert strengths["A"] == pytest.approx(0.8, abs=0.01)

    def test_strong_attacker_reduces_more(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 1.0, "B": 0.7})
        strengths = _compute_quad_strengths(praf, {})
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
        strengths = _compute_quad_strengths(praf, supports)
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

        s_weak = _compute_quad_strengths(praf_weak, {})
        s_strong = _compute_quad_strengths(praf_strong, {})

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
        s_weak = _compute_quad_strengths(praf, supports)

        praf2 = _make_praf(["A", "B"], [], {"A": 0.9, "B": 0.5})
        supports2 = {("A", "B"): 0.9}
        s_strong = _compute_quad_strengths(praf2, supports2)

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
        s_support = _compute_quad_strengths(praf_support, supports_only)

        # A attacks B
        praf_attack = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.5})
        s_attack = _compute_quad_strengths(praf_attack, {})

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
        strengths = _compute_quad_strengths(praf, {})
        for s in strengths.values():
            assert 0.0 <= s <= 1.0

    def test_many_attackers_bounded(self) -> None:
        args = ["T"] + [f"A{i}" for i in range(5)]
        defeats = [(f"A{i}", "T") for i in range(5)]
        scores = {"T": 0.9}
        for i in range(5):
            scores[f"A{i}"] = 0.9
        praf = _make_praf(args, defeats, scores)
        strengths = _compute_quad_strengths(praf, {})
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
        strengths = _compute_quad_strengths(praf, supports)
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
        strengths = _compute_quad_strengths(praf, supports)

        # B should be strengthened by A's support
        assert strengths["B"] > 0.5
        # C should be weakened because B (now stronger) attacks it
        assert strengths["C"] < 0.7


# ---------------------------------------------------------------------------
# Test 9: PrAF dispatch
# ---------------------------------------------------------------------------


class TestPrAFDispatch:
    """Public DF-QuAD dispatch uses explicit family names."""

    def test_dfquad_strategy_returns_result(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.6})
        result = compute_probabilistic_acceptance(
            praf,
            strategy="dfquad_quad",
            tau={"A": 0.8, "B": 0.6},
        )
        assert isinstance(result, PrAFResult)
        assert result.strategy_used == "dfquad_quad"
        assert result.samples is None
        assert result.confidence_interval_half is None
        assert "A" in result.acceptance_probs
        assert "B" in result.acceptance_probs

    def test_dfquad_dispatch_uses_praf_support_edges(self) -> None:
        """Public DF-QuAD dispatch must consume the PrAF support relation.

        Freedman-style gradual strengths are support-sensitive. A support-only
        QBAF should not collapse to the target's base score when invoked through
        compute_probabilistic_acceptance().
        """
        af = ArgumentationFramework(arguments=frozenset({"A", "B"}), defeats=frozenset())
        praf = ProbabilisticAF(
            framework=af,
            p_args={
                "A": 0.9,
                "B": 0.3,
            },
            p_defeats={},
            supports=frozenset({("A", "B")}),
            p_supports={("A", "B"): 0.8},
        )

        direct = compute_dfquad_quad_strengths(
            praf,
            {("A", "B"): praf.p_supports[("A", "B")]},
            tau={"A": 0.9, "B": 0.3},
        )
        dispatched = compute_probabilistic_acceptance(
            praf,
            strategy="dfquad_quad",
            tau={"A": 0.9, "B": 0.3},
        )

        assert dispatched.acceptance_probs["B"] == pytest.approx(direct["B"], abs=1e-9)
        assert dispatched.acceptance_probs["B"] > 0.3

    def test_dfquad_dispatch_respects_support_weight_changes(self) -> None:
        """Changing support weight should change the target's gradual strength."""
        af = ArgumentationFramework(arguments=frozenset({"A", "B"}), defeats=frozenset())
        weak = ProbabilisticAF(
            framework=af,
            p_args={
                "A": 0.9,
                "B": 0.3,
            },
            p_defeats={},
            supports=frozenset({("A", "B")}),
            p_supports={("A", "B"): 0.2},
        )
        strong = ProbabilisticAF(
            framework=af,
            p_args=weak.p_args,
            p_defeats={},
            supports=frozenset({("A", "B")}),
            p_supports={("A", "B"): 0.9},
        )

        weak_result = compute_probabilistic_acceptance(
            weak,
            strategy="dfquad_quad",
            tau={"A": 0.9, "B": 0.3},
        )
        strong_result = compute_probabilistic_acceptance(
            strong,
            strategy="dfquad_quad",
            tau={"A": 0.9, "B": 0.3},
        )

        assert strong_result.acceptance_probs["B"] > weak_result.acceptance_probs["B"]

    def test_dfquad_rejects_irrelevant_dung_semantics_argument(self) -> None:
        """DF-QuAD is a gradual semantics and should reject Dung labels."""
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.6})

        with pytest.raises(ValueError, match="DF-QuAD"):
            compute_probabilistic_acceptance(
                praf,
                strategy="dfquad_baf",
                semantics="stable",
            )

    def test_dfquad_strategy_name_must_be_explicit(self) -> None:
        praf = _make_praf(["A"], [], {"A": 0.8})

        with pytest.raises(ValueError, match="dfquad_quad.*dfquad_baf"):
            compute_probabilistic_acceptance(praf, strategy="dfquad")


def test_dfquad_quad_requires_explicit_tau() -> None:
    praf = _make_praf(["A"], [], {"A": 0.8})

    with pytest.raises(ValueError, match="tau"):
        compute_probabilistic_acceptance(praf, strategy="dfquad_quad")


def test_dfquad_quad_missing_tau_errors_cleanly() -> None:
    praf = _make_praf(["A", "B"], [("A", "B")], {"A": 0.8, "B": 0.6})

    with pytest.raises(ValueError, match="missing tau.*B"):
        compute_probabilistic_acceptance(
            praf,
            strategy="dfquad_quad",
            tau={"A": 0.8},
        )


def test_dfquad_baf_uses_fixed_neutral_0_5_for_isolated_arguments() -> None:
    praf = _make_praf(["A"], [], {"A": 0.9})

    result = compute_probabilistic_acceptance(praf, strategy="dfquad_baf")

    assert result.strategy_used == "dfquad_baf"
    assert result.acceptance_probs["A"] == pytest.approx(0.5, abs=1e-9)


def test_dfquad_quad_tau_varies_independently_of_praf_argument_probability() -> None:
    low_pa = _make_praf(["A"], [], {"A": 0.1})
    high_pa = _make_praf(["A"], [], {"A": 0.9})

    low_result = compute_probabilistic_acceptance(
        low_pa,
        strategy="dfquad_quad",
        tau={"A": 0.7},
    )
    high_result = compute_probabilistic_acceptance(
        high_pa,
        strategy="dfquad_quad",
        tau={"A": 0.7},
    )

    assert low_result.acceptance_probs["A"] == pytest.approx(0.7, abs=1e-9)
    assert high_result.acceptance_probs["A"] == pytest.approx(0.7, abs=1e-9)


def test_dfquad_baf_does_not_read_praf_argument_probability_as_base_score() -> None:
    low_pa = _make_praf(["A"], [], {"A": 0.1})
    high_pa = _make_praf(["A"], [], {"A": 0.9})

    low_result = compute_probabilistic_acceptance(low_pa, strategy="dfquad_baf")
    high_result = compute_probabilistic_acceptance(high_pa, strategy="dfquad_baf")

    assert low_result.acceptance_probs["A"] == pytest.approx(0.5, abs=1e-9)
    assert high_result.acceptance_probs["A"] == pytest.approx(0.5, abs=1e-9)


def test_dfquad_baf_isolated_argument_scores_0_5() -> None:
    praf = _make_praf(["A"], [], {"A": 0.2})

    result = compute_probabilistic_acceptance(praf, strategy="dfquad_baf")

    assert result.acceptance_probs["A"] == pytest.approx(0.5, abs=1e-9)


# ---------------------------------------------------------------------------
# Test 10: DF-QuAD vs deterministic for extreme case
# ---------------------------------------------------------------------------


class TestDFQuADVsDeterministic:
    """For A attacks B with base_score=1.0 for A, DF-QuAD should give
    A strength=1.0 and B strength=0.0 — matching grounded extension.
    """

    def test_deterministic_extreme(self) -> None:
        praf = _make_praf(["A", "B"], [("A", "B")], {"A": 1.0, "B": 1.0})
        strengths = _compute_quad_strengths(praf, {})
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


# ---------------------------------------------------------------------------
# Hypothesis property test: DF-QuAD output boundedness
# Per Freedman et al. (2025, p.3): all strengths in [0, 1]
# ---------------------------------------------------------------------------
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from argumentation.dung import ArgumentationFramework

def _small_praf_strategy_dfquad():
    """Strategy: build a small PrAF with 2-4 arguments, random attacks,
    random P_A opinions.  All P_D are dogmatic (certain defeats).
    """
    @st.composite
    def build(draw):
        n_args = draw(st.integers(min_value=2, max_value=4))
        arg_names = [f"arg{i}" for i in range(n_args)]

        p_args = {}
        for name in arg_names:
            p = draw(st.floats(min_value=0.05, max_value=0.95))
            p_args[name] = p

        attacks = set()
        for i, src in enumerate(arg_names):
            for j, tgt in enumerate(arg_names):
                if i != j and draw(st.booleans()):
                    attacks.add((src, tgt))

        af = ArgumentationFramework(
            arguments=frozenset(arg_names),
            defeats=frozenset(attacks),
            attacks=frozenset(attacks),
        )
        p_defeats = {edge: 1.0 for edge in attacks}

        return ProbabilisticAF(
            framework=af,
            p_args=p_args,
            p_defeats=p_defeats,
        )

    return build()


@st.composite
def _paired_quad_inputs(draw):
    praf = draw(_small_praf_strategy_dfquad())
    tau = {
        arg: draw(st.floats(min_value=0.0, max_value=1.0))
        for arg in sorted(praf.framework.arguments)
    }
    alt_p_args = {
        arg: draw(st.floats(min_value=0.05, max_value=0.95))
        for arg in sorted(praf.framework.arguments)
    }
    alt_praf = ProbabilisticAF(
        framework=praf.framework,
        p_args=alt_p_args,
        p_defeats=praf.p_defeats,
        p_attacks=praf.p_attacks,
        supports=praf.supports,
        p_supports=praf.p_supports,
        base_defeats=praf.base_defeats,
    )
    return praf, alt_praf, tau


@st.composite
def _isolated_prafs(draw):
    n_args = draw(st.integers(min_value=1, max_value=4))
    arg_names = [f"iso{idx}" for idx in range(n_args)]
    base_scores = {
        arg: draw(st.floats(min_value=0.05, max_value=0.95))
        for arg in arg_names
    }
    return _make_praf(arg_names, [], base_scores)


@st.composite
def _isolated_tau_pair(draw):
    pa = draw(st.floats(min_value=0.05, max_value=0.95))
    tau_left = draw(st.floats(min_value=0.0, max_value=1.0))
    tau_right = draw(st.floats(min_value=0.0, max_value=1.0))
    assume(abs(tau_left - tau_right) > 1e-6)
    return pa, tau_left, tau_right


@pytest.mark.property
@given(praf=_small_praf_strategy_dfquad())
@settings(deadline=None)
def test_dfquad_scores_bounded(praf):
    """All DF-QuAD scores must be in [0, 1].

    Per Freedman et al. (2025, p.3): the aggregation function guarantees
    output in [0,1] when base scores are in [0,1] and combined influence
    is in [-1,1].
    """
    result = compute_probabilistic_acceptance(praf, strategy="dfquad_baf")
    for arg, score in result.acceptance_probs.items():
        assert 0.0 <= score <= 1.0, f"arg {arg}: score={score} out of [0,1]"


@pytest.mark.property
@given(sample=_paired_quad_inputs())
@settings(deadline=None)
def test_dfquad_quad_property_ignores_praf_argument_probability_when_tau_is_fixed(sample):
    praf, alt_praf, tau = sample

    left = compute_probabilistic_acceptance(
        praf,
        strategy="dfquad_quad",
        tau=tau,
    )
    right = compute_probabilistic_acceptance(
        alt_praf,
        strategy="dfquad_quad",
        tau=tau,
    )

    assert left.acceptance_probs == right.acceptance_probs


@pytest.mark.property
@given(sample=_isolated_tau_pair())
@settings(deadline=None)
def test_dfquad_quad_property_changes_when_tau_changes_with_fixed_topology(sample):
    pa, tau_left, tau_right = sample
    praf = _make_praf(["A"], [], {"A": pa})

    left = compute_probabilistic_acceptance(
        praf,
        strategy="dfquad_quad",
        tau={"A": tau_left},
    )
    right = compute_probabilistic_acceptance(
        praf,
        strategy="dfquad_quad",
        tau={"A": tau_right},
    )

    assert left.acceptance_probs["A"] == pytest.approx(tau_left, abs=1e-9)
    assert right.acceptance_probs["A"] == pytest.approx(tau_right, abs=1e-9)
    assert left.acceptance_probs["A"] != pytest.approx(right.acceptance_probs["A"], abs=1e-6)


@pytest.mark.property
@given(praf=_isolated_prafs())
@settings(deadline=None)
def test_dfquad_baf_property_keeps_isolated_arguments_at_neutral_half(praf):
    result = compute_probabilistic_acceptance(praf, strategy="dfquad_baf")
    for score in result.acceptance_probs.values():
        assert score == pytest.approx(0.5, abs=1e-9)


# ── DF-QuAD monotonicity properties (Freedman et al. 2025 p.3-4) ──


from hypothesis import given, settings, assume
from hypothesis import strategies as st


@st.composite
def _monotonicity_scenario(draw):
    """Generate a target argument with some attackers/supporters, plus one extra arg.

    Returns (base_args, base_defeats, base_scores, extra_arg, target_arg).
    """
    n_existing = draw(st.integers(min_value=2, max_value=4))
    args = [f"a{i}" for i in range(n_existing)]
    target = args[0]

    base_scores = {
        a: draw(st.floats(min_value=0.1, max_value=0.9))
        for a in args
    }

    # Random attacks among existing args (not self-attacks)
    defeats = []
    for src in args[1:]:
        if draw(st.booleans()):
            defeats.append((src, target))

    extra = f"extra"
    extra_score = draw(st.floats(min_value=0.1, max_value=0.9))

    return args, defeats, base_scores, extra, extra_score, target


@pytest.mark.property
@given(scenario=_monotonicity_scenario())
@settings(deadline=None)
def test_dfquad_adding_attacker_never_increases_strength(scenario):
    """Adding an attacker to an argument should never increase its strength.

    Per Freedman et al. (2025, p.3): the aggregation function uses
    negative influence from attackers, so adding one can only decrease
    or maintain the target's strength.
    """
    args, defeats, base_scores, extra, extra_score, target = scenario

    # Baseline: without extra attacker
    praf_base = _make_praf(args, defeats, base_scores)
    tau_base = {a: base_scores[a] for a in args}
    result_base = compute_dfquad_quad_strengths(
        praf_base, {}, tau=tau_base,
    )
    strength_before = result_base[target]

    # With extra attacker
    all_args = args + [extra]
    all_defeats = defeats + [(extra, target)]
    all_scores = {**base_scores, extra: extra_score}
    praf_with = _make_praf(all_args, all_defeats, all_scores)
    tau_with = {a: all_scores[a] for a in all_args}
    result_with = compute_dfquad_quad_strengths(
        praf_with, {}, tau=tau_with,
    )
    strength_after = result_with[target]

    assert strength_after <= strength_before + 1e-9, (
        f"Adding attacker increased strength of {target}: "
        f"{strength_before} -> {strength_after}"
    )


@pytest.mark.property
@given(scenario=_monotonicity_scenario())
@settings(deadline=None)
def test_dfquad_adding_supporter_never_decreases_strength(scenario):
    """Adding a supporter to an argument should never decrease its strength.

    Per Freedman et al. (2025, p.3): the aggregation function uses
    positive influence from supporters, so adding one can only increase
    or maintain the target's strength.
    """
    args, defeats, base_scores, extra, extra_score, target = scenario

    # Baseline: without extra supporter
    praf_base = _make_praf(args, defeats, base_scores)
    tau_base = {a: base_scores[a] for a in args}
    result_base = compute_dfquad_quad_strengths(
        praf_base, {}, tau=tau_base,
    )
    strength_before = result_base[target]

    # With extra supporter (support weight = 1.0)
    all_args = args + [extra]
    all_scores = {**base_scores, extra: extra_score}
    praf_with = _make_praf(all_args, defeats, all_scores)
    tau_with = {a: all_scores[a] for a in all_args}
    supports = {(extra, target): 1.0}
    result_with = compute_dfquad_quad_strengths(
        praf_with, supports, tau=tau_with,
    )
    strength_after = result_with[target]

    assert strength_after >= strength_before - 1e-9, (
        f"Adding supporter decreased strength of {target}: "
        f"{strength_before} -> {strength_after}"
    )


@pytest.mark.property
@given(praf=_small_praf_strategy_dfquad())
@settings(deadline=None)
def test_dfquad_convergence_bounded(praf):
    """DF-QuAD computation should always terminate and produce valid scores.

    Per Freedman et al. (2025): acyclic QBAFs converge in one pass;
    cyclic graphs use iterative fixpoint with max 100 iterations.
    All scores must be in [0, 1].
    """
    result = compute_probabilistic_acceptance(praf, strategy="dfquad_baf")
    for arg, score in result.acceptance_probs.items():
        assert 0.0 - 1e-9 <= score <= 1.0 + 1e-9, (
            f"arg {arg}: score={score} out of [0,1]"
        )
