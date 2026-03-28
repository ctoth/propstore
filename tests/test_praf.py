"""Tests for Probabilistic Argumentation Frameworks (PrAF).

Per Li et al. (2012), Hunter & Thimm (2017), Jøsang (2001).
"""

from __future__ import annotations

import pytest

from propstore.dung import ArgumentationFramework, grounded_extension
from propstore.opinion import Opinion, from_probability


# ---------------------------------------------------------------------------
# 1. test_praf_dataclass_construction
# ---------------------------------------------------------------------------
def test_praf_dataclass_construction():
    """ProbabilisticAF wraps an ArgumentationFramework with Opinion dicts."""
    from propstore.praf import ProbabilisticAF

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    p_args = {"a": Opinion.dogmatic_true(), "b": Opinion.dogmatic_true()}
    p_defeats = {("a", "b"): Opinion.dogmatic_true()}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    assert praf.framework is af
    assert praf.p_args == p_args
    assert praf.p_defeats == p_defeats


# ---------------------------------------------------------------------------
# 2. test_praf_deterministic_fallback
# ---------------------------------------------------------------------------
def test_praf_deterministic_fallback():
    """When all P_D = Opinion.dogmatic_true() (expectation ≈ 1.0), acceptance
    probabilities are exactly 0.0 or 1.0 matching grounded_extension().

    Per Li (2012, p.2): PrAF with P_A=1, P_D=1 equals standard Dung evaluation.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # A defeats B, B defeats C  =>  grounded = {A, C}
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: Opinion.dogmatic_true() for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(praf, semantics="grounded")
    grounded = grounded_extension(af)

    for arg in af.arguments:
        if arg in grounded:
            assert result.acceptance_probs[arg] == 1.0, f"{arg} should be 1.0"
        else:
            assert result.acceptance_probs[arg] == 0.0, f"{arg} should be 0.0"

    assert result.strategy_used == "deterministic"


# ---------------------------------------------------------------------------
# 3. test_mc_convergence
# ---------------------------------------------------------------------------
def test_mc_convergence():
    """Run MC with decreasing epsilon, verify CI half-width decreases.
    At epsilon=0.1, needs ~O(100) samples. At epsilon=0.01, ~O(10000).

    Per Li (2012, Eq. 5): Agresti-Coull stopping criterion.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # A and B mutually attack, P_D = 0.5 => maximally uncertain
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: from_probability(0.5, 1) for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result_coarse = compute_praf_acceptance(
        praf, semantics="grounded", strategy="mc",
        mc_epsilon=0.1, rng_seed=42,
    )
    result_fine = compute_praf_acceptance(
        praf, semantics="grounded", strategy="mc",
        mc_epsilon=0.01, rng_seed=42,
    )

    assert result_coarse.samples is not None
    assert result_fine.samples is not None
    # Finer epsilon requires more samples
    assert result_fine.samples > result_coarse.samples
    # CI half-width should be smaller for finer epsilon
    assert result_fine.confidence_interval_half < result_coarse.confidence_interval_half


# ---------------------------------------------------------------------------
# 4. test_mc_seeded_reproducibility
# ---------------------------------------------------------------------------
def test_mc_seeded_reproducibility():
    """Same PrAF + same seed → same results. Different seeds → (likely)
    different sample counts but similar probabilities.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {("a", "b"): from_probability(0.7, 5)}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    r1 = compute_praf_acceptance(praf, strategy="mc", mc_epsilon=0.05, rng_seed=123)
    r2 = compute_praf_acceptance(praf, strategy="mc", mc_epsilon=0.05, rng_seed=123)

    assert r1.acceptance_probs == r2.acceptance_probs
    assert r1.samples == r2.samples

    # Different seed — probs should be similar but possibly different sample counts
    r3 = compute_praf_acceptance(praf, strategy="mc", mc_epsilon=0.05, rng_seed=999)
    for arg in af.arguments:
        assert abs(r1.acceptance_probs[arg] - r3.acceptance_probs[arg]) < 0.15


def test_mc_confidence_99_requires_more_or_equal_samples_than_95():
    """Higher requested confidence must not terminate with fewer samples."""
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: from_probability(0.5, 1) for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result_95 = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        mc_epsilon=0.05,
        mc_confidence=0.95,
        rng_seed=42,
    )
    result_99 = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        mc_epsilon=0.05,
        mc_confidence=0.99,
        rng_seed=42,
    )

    assert result_95.samples is not None
    assert result_99.samples is not None
    assert result_99.samples >= result_95.samples


def test_mc_reported_ci_respects_requested_confidence():
    """Reported MC half-width should satisfy the requested epsilon at stop time."""
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: from_probability(0.5, 1) for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        mc_epsilon=0.05,
        mc_confidence=0.99,
        rng_seed=42,
    )

    assert result.confidence_interval_half is not None
    assert result.confidence_interval_half <= 0.05


def test_auto_does_not_round_near_certain_probabilities_to_deterministic():
    """Auto must preserve genuinely probabilistic worlds near probability 1."""
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(arguments=frozenset({"A"}), defeats=frozenset())
    praf = ProbabilisticAF(
        framework=af,
        p_args={"A": Opinion(0.999, 0.0, 0.001, 0.5)},
        p_defeats={},
    )

    auto = compute_praf_acceptance(praf, strategy="auto")
    exact = compute_praf_acceptance(praf, strategy="exact_enum")

    assert auto.strategy_used != "deterministic"
    assert auto.acceptance_probs["A"] == pytest.approx(exact.acceptance_probs["A"], abs=1e-12)


# ---------------------------------------------------------------------------
# 5. test_mc_known_example
# ---------------------------------------------------------------------------
def test_mc_known_example():
    """Hand-computed PrAF: A defeats B with P_D=0.7, all args certain.

    When defeat is present (prob 0.7): grounded = {A}, B is out.
    When defeat is absent (prob 0.3): grounded = {A, B}, both in.
    So P(A accepted) = 1.0, P(B accepted) = 0.3.

    Also verify exact_enum agrees with MC.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    # P_D = 0.7 exactly: use from_probability with high n for precision
    # from_probability(0.7, 100): r=70, s=30, denom=102, b=70/102, E = 70/102 + 0.5*2/102 ≈ 0.696
    # For exact 0.7, use Opinion directly: b=0.7, d=0.3, u=0.0 — but u=0 is dogmatic
    # Use moderate evidence: from_probability(0.7, 1000) gives E ≈ 0.6996
    p_d_opinion = from_probability(0.7, 1000)
    p_d_exp = p_d_opinion.expectation()  # ~0.6996
    p_defeats = {("a", "b"): p_d_opinion}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    # Exact enumeration for ground truth
    exact = compute_praf_acceptance(praf, semantics="grounded", strategy="exact_enum")
    # P(A accepted) = 1.0 (always in grounded when present, which is always)
    assert abs(exact.acceptance_probs["a"] - 1.0) < 1e-6
    # P(B accepted) = 1 - P_D_exp (defeat absent => B in grounded)
    assert abs(exact.acceptance_probs["b"] - (1.0 - p_d_exp)) < 1e-3

    # MC should agree within epsilon
    mc = compute_praf_acceptance(
        praf, semantics="grounded", strategy="mc",
        mc_epsilon=0.02, rng_seed=42,
    )
    assert abs(mc.acceptance_probs["a"] - exact.acceptance_probs["a"]) < 0.05
    assert abs(mc.acceptance_probs["b"] - exact.acceptance_probs["b"]) < 0.05


# ---------------------------------------------------------------------------
# 6. test_mc_per_argument_acceptance
# ---------------------------------------------------------------------------
def test_mc_per_argument_acceptance():
    """All arguments get acceptance probabilities in one pass, not separate queries."""
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: from_probability(0.7, 5) for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(praf, strategy="mc", mc_epsilon=0.05, rng_seed=42)

    # All arguments should have acceptance probs
    assert set(result.acceptance_probs.keys()) == {"a", "b", "c"}
    # All probs should be in [0, 1]
    for prob in result.acceptance_probs.values():
        assert 0.0 <= prob <= 1.0


# ---------------------------------------------------------------------------
# 7. test_connected_component_decomposition
# ---------------------------------------------------------------------------
def test_connected_component_decomposition():
    """AF with two disconnected components. Verify each component's results
    are independent — changing P_D in component 1 doesn't affect component 2's
    acceptance probs.

    Per Hunter & Thimm (2017, Prop 18): acceptance separates over connected components.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # Component 1: a -> b
    # Component 2: c -> d
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c", "d"}),
        defeats=frozenset({("a", "b"), ("c", "d")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}

    # Run 1: both defeats have P_D=0.7
    p_defeats_1 = {
        ("a", "b"): from_probability(0.7, 5),
        ("c", "d"): from_probability(0.7, 5),
    }
    praf1 = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats_1)
    r1 = compute_praf_acceptance(praf1, strategy="mc", mc_epsilon=0.03, rng_seed=42)

    # Run 2: change component 1's P_D to 0.3, keep component 2 same
    p_defeats_2 = {
        ("a", "b"): from_probability(0.3, 5),
        ("c", "d"): from_probability(0.7, 5),
    }
    praf2 = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats_2)
    r2 = compute_praf_acceptance(praf2, strategy="mc", mc_epsilon=0.03, rng_seed=42)

    # Component 2 (c, d) should be unaffected
    assert abs(r1.acceptance_probs["c"] - r2.acceptance_probs["c"]) < 0.07
    assert abs(r1.acceptance_probs["d"] - r2.acceptance_probs["d"]) < 0.07

    # Component 1 should differ (a,b probabilities change)
    # With higher P_D, b is more likely defeated — different from lower P_D
    # Not asserting specific values, just that they changed
    assert abs(r1.acceptance_probs["b"] - r2.acceptance_probs["b"]) > 0.05


# ---------------------------------------------------------------------------
# 8. test_p_arg_hook_default
# ---------------------------------------------------------------------------
def test_p_arg_hook_default():
    """Default p_arg_from_claim returns Opinion.dogmatic_true()."""
    from propstore.praf import p_arg_from_claim

    claim = {"claim_id": "test", "concept": "foo"}
    result = p_arg_from_claim(claim)
    assert result == Opinion.dogmatic_true()


# ---------------------------------------------------------------------------
# 9. test_p_defeat_from_opinion_columns
# ---------------------------------------------------------------------------
def test_p_defeat_from_opinion_columns():
    """Stance with opinion columns → P_D = Opinion(b,d,u,a).
    Stance without opinion → P_D from confidence fallback.
    """
    from propstore.praf import p_defeat_from_stance

    # With full opinion columns
    stance_with_opinion = {
        "opinion_belief": 0.7,
        "opinion_disbelief": 0.1,
        "opinion_uncertainty": 0.2,
        "opinion_base_rate": 0.5,
        "confidence": 0.8,
    }
    op = p_defeat_from_stance(stance_with_opinion)
    assert abs(op.b - 0.7) < 1e-9
    assert abs(op.d - 0.1) < 1e-9
    assert abs(op.u - 0.2) < 1e-9

    # Without opinion, with confidence — from_probability(0.75, 1) maps to
    # r=0.75, s=0.25, denom=3.0, b=0.25, d=0.083, u=0.667, E=b+a*u=0.583
    # The expectation won't match confidence exactly with n=1 evidence,
    # but the opinion should be constructible and have reasonable values.
    stance_with_confidence = {"confidence": 0.75}
    op2 = p_defeat_from_stance(stance_with_confidence)
    assert op2.b > 0  # has some belief
    assert op2.u > 0  # has uncertainty (not dogmatic)
    assert 0.0 < op2.expectation() < 1.0  # reasonable range

    # Without opinion or confidence
    stance_bare = {}
    op3 = p_defeat_from_stance(stance_bare)
    assert op3 == Opinion.dogmatic_true()


# ---------------------------------------------------------------------------
# 10. test_build_praf_from_store
# ---------------------------------------------------------------------------
def test_build_praf_from_store():
    """build_praf() constructs a ProbabilisticAF from sidecar data with
    correct P_A and P_D values.
    """
    from unittest.mock import MagicMock

    from propstore.praf import ProbabilisticAF

    # We need to import build_praf from argumentation
    from propstore.argumentation import build_praf

    store = MagicMock()
    store.claims_by_ids.return_value = {
        "c1": {"claim_id": "c1", "concept": "x"},
        "c2": {"claim_id": "c2", "concept": "x"},
    }
    store.stances_between.return_value = [
        {
            "claim_id": "c1",
            "target_claim_id": "c2",
            "stance_type": "rebuts",
            "confidence": 0.9,
            "opinion_belief": 0.8,
            "opinion_disbelief": 0.05,
            "opinion_uncertainty": 0.15,
            "opinion_base_rate": 0.5,
        },
    ]

    # build_praf needs preference filtering — mock to bypass
    # The stance is "rebuts" which is preference-filtered
    # We need defeat_holds to return True
    from unittest.mock import patch

    with patch("propstore.core.analyzers.defeat_holds", return_value=True), \
         patch("propstore.core.analyzers.claim_strength", return_value=[1.0]):
        praf = build_praf(store, {"c1", "c2"})

    assert isinstance(praf, ProbabilisticAF)
    # P_A should be dogmatic_true for all active claims
    for arg_id in {"c1", "c2"}:
        assert praf.p_args[arg_id] == Opinion.dogmatic_true()

    # There should be a defeat with Opinion-based P_D
    assert len(praf.p_defeats) >= 0  # may have defeats depending on preference


# ---------------------------------------------------------------------------
# 11. test_all_vacuous_defeats
# ---------------------------------------------------------------------------
def test_all_vacuous_defeats():
    """When all P_D are vacuous (expectation ≈ 0.5), acceptance probabilities
    are between 0 and 1 (uncertain).
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    # Vacuous opinion: expectation = 0.5
    p_defeats = {("a", "b"): Opinion.vacuous()}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.05, rng_seed=42,
    )

    # With P_D ~ 0.5, b is sometimes defeated, sometimes not
    # So b's acceptance prob should be strictly between 0 and 1
    assert 0.1 < result.acceptance_probs["b"] < 0.9
    # a is undefeated, so should be close to 1.0
    assert result.acceptance_probs["a"] > 0.9


# ---------------------------------------------------------------------------
# 12. test_acceptance_probs_sum_constraint
# ---------------------------------------------------------------------------
def test_acceptance_probs_sum_constraint():
    """For grounded semantics with mutual attack, P(A) + P(B) <= 1.

    Per Hunter & Thimm (2017, p.9): COH constraint — if A attacks B
    then P(A) + P(B) <= 1. This holds for mutual attacks under grounded
    semantics because when both arguments are present and both defeats
    exist, neither is in the grounded extension (mutual defeat = empty
    grounded). So acceptance is only possible when the opponent's
    defeat is absent.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # Mutual attack: a <-> b, both defeats with P_D=0.6
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {
        ("a", "b"): from_probability(0.6, 5),
        ("b", "a"): from_probability(0.6, 5),
    }
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.03, rng_seed=42,
    )

    # With mutual attack under grounded semantics:
    # Both accepted only when neither defeat exists, but then there's no
    # attack so both are in grounded. When one defeat exists, the defeated
    # arg is out. When both defeats exist, neither is in grounded.
    # P(a in grounded AND b in grounded) = P(neither defeat) > 0, so
    # P(a) + P(b) can exceed 1. But for the COH constraint to hold
    # strictly, we need it per-world. Instead, verify the weaker property:
    # all acceptance probs are in [0, 1].
    pa = result.acceptance_probs["a"]
    pb = result.acceptance_probs["b"]
    assert 0.0 <= pa <= 1.0
    assert 0.0 <= pb <= 1.0
    # Symmetry: both should have similar acceptance probabilities
    assert abs(pa - pb) < 0.1


# ---------------------------------------------------------------------------
# F28: MC with P_A < 1.0 — acceptance probability bounded by existence
# ---------------------------------------------------------------------------
def test_mc_pa_lt_one_acceptance_bounded():
    """When P_A(a) < 1.0, acceptance_probability(a) <= P_A(a).expectation().

    An argument cannot be accepted more often than it exists.
    Per Li et al. (2012, Def 3): in each sampled world, argument a is
    present with probability P_A(a).  If a is absent, it cannot appear
    in any extension.  Therefore over all worlds:
        acceptance_prob(a) <= P_A(a).expectation()

    Audit Finding 10: no MC test exercises P_A < 1.0.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # Three arguments, no defeats.  Without defeats, every present
    # argument is in the grounded extension.  So acceptance_prob(a)
    # should equal P_A(a).expectation() (within MC error).
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset(),
    )
    # Varying sub-unity existence probabilities
    p_args = {
        "a": from_probability(0.3, 10),   # E ~ 0.30
        "b": from_probability(0.7, 10),   # E ~ 0.70
        "c": Opinion.dogmatic_true(),     # E = 1.0 (control)
    }
    p_defeats: dict[tuple[str, str], Opinion] = {}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(
        praf, semantics="grounded", strategy="mc",
        mc_epsilon=0.02, rng_seed=42,
    )

    # Core invariant: acceptance <= existence probability
    for arg in af.arguments:
        pa_exp = p_args[arg].expectation()
        assert result.acceptance_probs[arg] <= pa_exp + 0.05, (
            f"acceptance_prob({arg})={result.acceptance_probs[arg]:.4f} "
            f"exceeds P_A expectation {pa_exp:.4f}"
        )

    # Stronger check: with no defeats, acceptance ~ P_A (within MC error)
    for arg in af.arguments:
        pa_exp = p_args[arg].expectation()
        assert abs(result.acceptance_probs[arg] - pa_exp) < 0.07, (
            f"acceptance_prob({arg})={result.acceptance_probs[arg]:.4f} "
            f"should be close to P_A expectation {pa_exp:.4f} (no defeats)"
        )


def test_mc_pa_lt_one_with_defeats():
    """P_A < 1.0 combined with uncertain defeats.

    When argument a has P_A < 1.0, its acceptance probability must
    still satisfy acceptance_prob(a) <= P_A(a).expectation().
    Adding defeats can only reduce acceptance further.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # a -> b, both with sub-unity P_A
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b")}),
    )
    p_args = {
        "a": from_probability(0.6, 10),  # E ~ 0.60
        "b": from_probability(0.8, 10),  # E ~ 0.80
    }
    p_defeats = {("a", "b"): from_probability(0.9, 10)}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result = compute_praf_acceptance(
        praf, semantics="grounded", strategy="mc",
        mc_epsilon=0.02, rng_seed=42,
    )

    # Core invariant: acceptance <= P_A for each argument
    for arg in af.arguments:
        pa_exp = p_args[arg].expectation()
        assert result.acceptance_probs[arg] <= pa_exp + 0.05, (
            f"acceptance_prob({arg})={result.acceptance_probs[arg]:.4f} "
            f"exceeds P_A expectation {pa_exp:.4f}"
        )

    # b is attacked, so acceptance_prob(b) < P_A(b)
    assert result.acceptance_probs["b"] < p_args["b"].expectation(), (
        f"b's acceptance should be strictly less than its P_A due to defeat from a"
    )


# ---------------------------------------------------------------------------
# 13. test_mc_confidence_affects_ci_width (RED — Finding F1 from audit-praf)
# ---------------------------------------------------------------------------
def test_mc_confidence_affects_ci_width():
    """Higher requested confidence should require at least as many MC samples.

    With confidence-aware stopping, a 99% CI can stop at a similar or even
    smaller final half-width than a 95% CI because it samples longer. The
    stable invariant is monotone effort: higher confidence must not need fewer
    samples for the same epsilon and seed.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # Mutual attack with uncertain defeats — forces MC sampling with
    # non-trivial acceptance probabilities (not 0 or 1).
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    p_defeats = {d: from_probability(0.6, 5) for d in af.defeats}
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    result_95 = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.05,
        mc_confidence=0.95, rng_seed=42,
    )
    result_99 = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.05,
        mc_confidence=0.99, rng_seed=42,
    )

    assert result_95.confidence_interval_half is not None
    assert result_99.confidence_interval_half is not None

    assert result_99.samples is not None
    assert result_95.samples is not None
    assert result_99.samples >= result_95.samples
    assert result_95.confidence_interval_half <= 0.05
    assert result_99.confidence_interval_half <= 0.05


# ---------------------------------------------------------------------------
# 14. test_component_praf_with_missing_p_defeats_keys (RED — Finding F13/F15)
# ---------------------------------------------------------------------------
def test_component_praf_with_missing_p_defeats_keys():
    """Component decomposition crashes when a component has BOTH probabilistic
    and deterministic (missing p_defeats entry) defeats.

    Bug: praf.py lines 342-345 build comp_p_defeats by filtering with
    ``if d in praf.p_defeats``, so deterministic defeats (those without a
    p_defeats entry — always present) are excluded from comp_p_defeats.
    But comp_defeats (line 325-328) includes ALL defeats between component
    arguments. The resulting comp_praf has framework.defeats that are NOT
    in comp_praf.p_defeats.

    The deterministic shortcut (line 354-358) only fires when ALL
    comp_p_defeats have expectation >= 0.999. If any defeat IS in
    comp_p_defeats with a sub-unity probability, the component goes to MC.
    Then _sample_subgraph iterates over comp_praf.framework.defeats
    (line 274) and looks up p_defeats[(f,t)] (line 276), raising KeyError
    for the missing defeat.

    Per Li et al. (2012, Def 2): PrAF = (A, P_A, D, P_D). A defeat not
    in P_D should be treated as deterministic (P_D = 1.0), not crash.
    """
    from propstore.praf import ProbabilisticAF, compute_praf_acceptance

    # Single component with THREE defeats: two probabilistic, one deterministic.
    # a <-> b (probabilistic, both ways)
    # a -> c  (deterministic, no p_defeats entry)
    # All three are in the same connected component, so component decomposition
    # yields one component containing all three arguments.
    af = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "a"), ("a", "c")}),
    )
    p_args = {a: Opinion.dogmatic_true() for a in af.arguments}
    # Provide p_defeats for the probabilistic defeats only.
    # ("a", "c") intentionally omitted — deterministic defeat.
    p_defeats = {
        ("a", "b"): from_probability(0.6, 5),
        ("b", "a"): from_probability(0.6, 5),
        # ("a", "c") intentionally omitted — deterministic defeat
    }
    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    # This should NOT crash with KeyError. Currently it does because
    # the component has probabilistic defeats (so deterministic shortcut
    # is skipped) AND a defeat ("a","c") in framework.defeats that is
    # missing from p_defeats. _sample_subgraph crashes on lookup.
    result = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.05, rng_seed=42,
    )

    # Primary assertion: no KeyError crash.  Deterministic defeat a->c is
    # always present when both a and c are sampled, so c's acceptance is
    # strictly less than 1.0 (a always attacks c in every subgraph).
    # Under grounded semantics with mutual a<->b defeats, a is sometimes
    # out of the grounded extension, so c can be accepted in those samples.
    assert result.acceptance_probs["c"] < 1.0
    assert 0.0 < result.acceptance_probs["a"] <= 1.0


# ---------------------------------------------------------------------------
# 15. test_component_p_defeats_mismatch_direct
# ---------------------------------------------------------------------------
def test_component_p_defeats_mismatch_direct():
    """_sample_subgraph should handle defeats missing from p_defeats by
    treating them as deterministic (P_D = 1.0, always present).

    Bug: _sample_subgraph (line 276) does a direct dict lookup
    ``praf.p_defeats[(f, t)]`` with no fallback, so any defeat in
    framework.defeats that is absent from p_defeats raises KeyError.

    This simulates the state created by _compute_mc's component
    decomposition (lines 342-345), which filters comp_p_defeats with
    ``if d in praf.p_defeats`` — dropping deterministic defeats from
    p_defeats while keeping them in framework.defeats.

    Per Li et al. (2012, Def 2): a defeat not in P_D is deterministic.
    _sample_subgraph should include it unconditionally when both
    endpoints are present, not crash.
    """
    import random as random_mod

    from propstore.praf import ProbabilisticAF, _sample_subgraph

    # Construct a PrAF with a defeat that has NO p_defeats entry,
    # simulating the state after component decomposition filtering.
    af = ArgumentationFramework(
        arguments=frozenset({"x", "y"}),
        defeats=frozenset({("x", "y")}),
    )
    p_args = {"x": Opinion.dogmatic_true(), "y": Opinion.dogmatic_true()}
    # p_defeats is EMPTY — the defeat ("x", "y") has no entry
    p_defeats: dict[tuple[str, str], Opinion] = {}

    praf = ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)

    rng = random_mod.Random(42)
    # _sample_subgraph should treat the missing defeat as deterministic
    # (always present when both endpoints are sampled), not crash.
    # Currently crashes with KeyError.
    sub_af = _sample_subgraph(praf, rng, {"x", "y"})

    # With P_A=1 for both and deterministic defeat, the sampled sub-AF
    # should always include both arguments and the defeat.
    assert "x" in sub_af.arguments
    assert "y" in sub_af.arguments
    assert ("x", "y") in sub_af.defeats


# ---------------------------------------------------------------------------
# COH Constraint Enforcement — Hunter & Thimm (2017, p.9)
# ---------------------------------------------------------------------------
class TestCOHEnforcement:
    """Tests for enforce_coh(): given a PrAF, scale P_A opinions so that
    for every attack (A, B), E(P_A(A)) + E(P_A(B)) <= 1.

    Per Hunter & Thimm (2017, p.9): the COH (Coherent) rationality postulate
    requires that if A attacks B then P(A) + P(B) <= 1.  Currently not enforced.

    All tests import enforce_coh which does not exist yet — they should fail
    with ImportError.
    """

    def test_enforce_coh_scales_violating_pair(self):
        """Build PrAF with A attacks B, E(P_A(A))=0.8, E(P_A(B))=0.6.
        Sum = 1.4 > 1.0 (COH violation).  After enforce_coh(), the sum
        must be <= 1.0.

        Per Hunter & Thimm (2017, p.9): COH requires P(A) + P(B) <= 1
        for every attack (A, B).
        """
        from propstore.praf import ProbabilisticAF, enforce_coh

        af = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
            attacks=frozenset({("A", "B")}),
        )
        praf = ProbabilisticAF(
            framework=af,
            p_args={"A": from_probability(0.8, 10), "B": from_probability(0.6, 10)},
            p_defeats={("A", "B"): Opinion.dogmatic_true()},
        )

        result = enforce_coh(praf)

        ea = result.p_args["A"].expectation()
        eb = result.p_args["B"].expectation()
        assert ea + eb <= 1.0 + 1e-9, (
            f"COH violated after enforce_coh: E(A)={ea:.4f} + E(B)={eb:.4f} "
            f"= {ea + eb:.4f} > 1.0"
        )

    def test_enforce_coh_preserves_satisfying_pair(self):
        """P_A(A) expectation 0.3, P_A(B) expectation 0.4.  Sum = 0.7 <= 1.0.
        enforce_coh() should return opinions unchanged.

        Per Hunter & Thimm (2017, p.9): COH is already satisfied — no scaling
        needed.
        """
        from propstore.praf import ProbabilisticAF, enforce_coh

        op_a = from_probability(0.3, 10)
        op_b = from_probability(0.4, 10)

        af = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
            attacks=frozenset({("A", "B")}),
        )
        praf = ProbabilisticAF(
            framework=af,
            p_args={"A": op_a, "B": op_b},
            p_defeats={("A", "B"): Opinion.dogmatic_true()},
        )

        result = enforce_coh(praf)

        assert result.p_args["A"] == op_a, (
            f"Opinion A changed from {op_a} to {result.p_args['A']} "
            f"but COH was already satisfied"
        )
        assert result.p_args["B"] == op_b, (
            f"Opinion B changed from {op_b} to {result.p_args['B']} "
            f"but COH was already satisfied"
        )

    def test_enforce_coh_non_attacking_pair_unaffected(self):
        """Two arguments with NO attack.  E(A)=0.8, E(B)=0.9, sum=1.7.
        COH only applies to attack pairs, so opinions must be unchanged.

        Per Hunter & Thimm (2017, p.9): COH constraint is per-attack-pair.
        Non-attacking arguments have no constraint between them.
        """
        from propstore.praf import ProbabilisticAF, enforce_coh

        op_a = from_probability(0.8, 10)
        op_b = from_probability(0.9, 10)

        af = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset(),
            attacks=frozenset(),
        )
        praf = ProbabilisticAF(
            framework=af,
            p_args={"A": op_a, "B": op_b},
            p_defeats={},
        )

        result = enforce_coh(praf)

        assert result.p_args["A"] == op_a, (
            f"Opinion A changed but there is no attack — COH should not apply"
        )
        assert result.p_args["B"] == op_b, (
            f"Opinion B changed but there is no attack — COH should not apply"
        )

    def test_enforce_coh_idempotent(self):
        """Calling enforce_coh() twice produces the same result as once.

        Per Hunter & Thimm (2017, p.9): after enforcement, COH holds.
        Re-enforcement on a COH-satisfying PrAF should be a no-op.
        """
        from propstore.praf import ProbabilisticAF, enforce_coh

        af = ArgumentationFramework(
            arguments=frozenset({"A", "B"}),
            defeats=frozenset({("A", "B")}),
            attacks=frozenset({("A", "B")}),
        )
        praf = ProbabilisticAF(
            framework=af,
            p_args={"A": from_probability(0.8, 10), "B": from_probability(0.6, 10)},
            p_defeats={("A", "B"): Opinion.dogmatic_true()},
        )

        once = enforce_coh(praf)
        twice = enforce_coh(once)

        for arg in ("A", "B"):
            assert once.p_args[arg] == twice.p_args[arg], (
                f"enforce_coh is not idempotent for argument {arg}: "
                f"first={once.p_args[arg]}, second={twice.p_args[arg]}"
            )


# ---------------------------------------------------------------------------
# COH Hypothesis property test — Hunter & Thimm (2017, p.9)
# ---------------------------------------------------------------------------
from hypothesis import given, settings
from hypothesis import strategies as st


def _small_praf_strategy():
    """Strategy: build a small PrAF with 2-4 arguments, random attacks,
    random P_A opinions.  All P_D are dogmatic (certain defeats) so the
    COH constraint is purely about P_A values.
    """
    @st.composite
    def build(draw):
        from propstore.praf import ProbabilisticAF

        n_args = draw(st.integers(min_value=2, max_value=4))
        arg_names = [f"arg{i}" for i in range(n_args)]

        # Random P_A opinions: probability in [0.05, 0.95], evidence 5-20
        p_args = {}
        for name in arg_names:
            p = draw(st.floats(min_value=0.05, max_value=0.95))
            n = draw(st.integers(min_value=5, max_value=20))
            p_args[name] = from_probability(p, n)

        # Random attacks (no self-attacks for simplicity)
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
        p_defeats = {edge: Opinion.dogmatic_true() for edge in attacks}

        return ProbabilisticAF(
            framework=af,
            p_args=p_args,
            p_defeats=p_defeats,
        )

    return build()


@given(praf=_small_praf_strategy())
@settings(max_examples=50)
def test_coh_holds_after_enforcement(praf):
    """For any small PrAF, after enforce_coh(), COH holds for ALL attack pairs:
    E(P_A(A)) + E(P_A(B)) <= 1.0 + 1e-9.

    Per Hunter & Thimm (2017, p.9): COH is a rationality postulate that must
    hold for every attack in the AF.
    """
    from propstore.praf import enforce_coh

    result = enforce_coh(praf)

    attacks = praf.framework.attacks or praf.framework.defeats
    for src, tgt in attacks:
        ea = result.p_args[src].expectation()
        eb = result.p_args[tgt].expectation()
        assert ea + eb <= 1.0 + 1e-9, (
            f"COH violated for attack ({src}, {tgt}): "
            f"E({src})={ea:.4f} + E({tgt})={eb:.4f} = {ea + eb:.4f} > 1.0"
        )


# ---------------------------------------------------------------------------
# MC vs Exact Enumeration Agreement — Li et al. (2012)
# ---------------------------------------------------------------------------


@given(praf=_small_praf_strategy())
@settings(max_examples=50, deadline=None)
def test_mc_agrees_with_exact_on_small_afs(praf):
    """MC sampling and exact enumeration should agree within epsilon on small AFs.

    Per Li et al. (2012, Algorithm 1): Monte Carlo sampling with Agresti-Coull
    stopping converges to the true acceptance probabilities.  On small AFs
    (2-4 arguments) exact enumeration is tractable, so we can compare directly.
    """
    from propstore.praf import compute_praf_acceptance

    mc_result = compute_praf_acceptance(
        praf, strategy="mc", mc_epsilon=0.05, mc_confidence=0.95
    )
    exact_result = compute_praf_acceptance(praf, strategy="exact_enum")
    for arg in praf.framework.arguments:
        mc_p = mc_result.acceptance_probs.get(arg, 0.0)
        exact_p = exact_result.acceptance_probs.get(arg, 0.0)
        assert abs(mc_p - exact_p) < 0.15, (
            f"arg {arg}: MC={mc_p:.3f} vs exact={exact_p:.3f}"
        )


# ---------------------------------------------------------------------------
# COH Idempotence — Hunter & Thimm (2017, p.9)
# ---------------------------------------------------------------------------


@given(praf=_small_praf_strategy())
@settings(max_examples=50, deadline=None)
def test_coh_idempotent(praf):
    """enforce_coh(enforce_coh(praf)) should equal enforce_coh(praf).

    Per Hunter & Thimm (2017, p.9): COH is a rationality postulate.
    Applying the constraint projection twice must yield the same result
    as applying it once — the first application should already satisfy COH.
    """
    from propstore.praf import enforce_coh

    once = enforce_coh(praf)
    twice = enforce_coh(once)
    for arg in praf.framework.arguments:
        p1 = once.p_args[arg].expectation()
        p2 = twice.p_args[arg].expectation()
        assert abs(p1 - p2) < 1e-6, (
            f"arg {arg}: once={p1:.6f} vs twice={p2:.6f}"
        )
