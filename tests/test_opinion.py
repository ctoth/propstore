"""Tests for propstore.opinion — Jøsang 2001 subjective logic operations."""

import math

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.opinion import (
    BetaEvidence,
    Opinion,
    ccf,
    consensus,
    consensus_pair,
    discount,
    from_evidence,
    from_probability,
    fuse,
    wbf,
    _TOL,
)


# --- Helpers ---

def approx(val, abs=1e-7):
    return pytest.approx(val, abs=abs)


# --- 1. b + d + u == 1 for all valid opinions ---

class TestBDUSum:
    def test_vacuous(self):
        o = Opinion.vacuous()
        assert o.b + o.d + o.u == approx(1.0)

    def test_dogmatic_true(self):
        o = Opinion.dogmatic_true()
        assert o.b + o.d + o.u == approx(1.0)

    def test_dogmatic_false(self):
        o = Opinion.dogmatic_false()
        assert o.b + o.d + o.u == approx(1.0)

    def test_arbitrary(self):
        o = Opinion(0.3, 0.2, 0.5, 0.6)
        assert o.b + o.d + o.u == approx(1.0)

    def test_rejects_invalid_sum(self):
        with pytest.raises(ValueError, match="b \\+ d \\+ u"):
            Opinion(0.5, 0.5, 0.5)


# --- 2. 0 < a < 1 for all non-degenerate opinions ---

class TestBaseRate:
    def test_a_zero_rejected(self):
        with pytest.raises(ValueError, match="a="):
            Opinion(0.5, 0.3, 0.2, 0.0)

    def test_a_one_rejected(self):
        with pytest.raises(ValueError, match="a="):
            Opinion(0.5, 0.3, 0.2, 1.0)

    def test_a_valid(self):
        o = Opinion(0.5, 0.3, 0.2, 0.7)
        assert 0.0 < o.a < 1.0


# --- 3. E(ω) = b + a*u is in [0, 1] ---

class TestExpectation:
    def test_vacuous(self):
        o = Opinion.vacuous(a=0.3)
        assert o.expectation() == approx(0.3)

    def test_dogmatic_true(self):
        assert Opinion.dogmatic_true().expectation() == approx(1.0)

    def test_dogmatic_false(self):
        assert Opinion.dogmatic_false().expectation() == approx(0.0)

    def test_in_unit_interval(self):
        o = Opinion(0.3, 0.2, 0.5, 0.6)
        e = o.expectation()
        assert 0.0 <= e <= 1.0
        assert e == approx(0.3 + 0.6 * 0.5)


# --- 4. E(ω_x ∧ ω_y) == E(ω_x) * E(ω_y) ---

class TestConjunctionExpectation:
    """E(x AND y) == E(x)*E(y) (Jøsang Proof 5, p.17).

    The binary conjunction expectation identity holds when operands are
    dogmatic (u=0, so E=b) or when base rates are 0.5 with the adjusted
    conjunction base rate. We test the structural formula directly and
    verify the identity for dogmatic and evidence-saturated cases.
    """

    def test_product_rule_dogmatic(self):
        """Dogmatic opinions: u=0 so E=b, conjunction b = bx*by."""
        x = Opinion(0.7, 0.3, 0.0, 0.5)
        y = Opinion(0.4, 0.6, 0.0, 0.5)
        conj = x & y
        assert conj.expectation() == approx(x.expectation() * y.expectation())

    def test_product_rule_high_evidence(self):
        """With very high evidence (low u), expectation approaches b, product rule approximately holds."""
        x = from_probability(0.75, 1000)
        y = from_probability(0.60, 1000)
        conj = x & y
        # With near-zero u, this should be very close
        assert conj.expectation() == approx(x.expectation() * y.expectation(), abs=0.01)

    def test_conjunction_produces_valid_opinion(self):
        x = Opinion(0.6, 0.1, 0.3, 0.5)
        y = Opinion(0.4, 0.2, 0.4, 0.5)
        conj = x & y
        assert conj.b + conj.d + conj.u == approx(1.0)
        assert 0.0 <= conj.expectation() <= 1.0


# --- 5. E(ω_x ∨ ω_y) == E(ω_x) + E(ω_y) - E(ω_x)*E(ω_y) ---

class TestDisjunctionExpectation:
    """E(x OR y) == E(x) + E(y) - E(x)*E(y) (Jøsang Proof 5, p.17).

    Like conjunction, the identity holds exactly for dogmatic opinions
    and approximately for high-evidence opinions.
    """

    def test_inclusion_exclusion_dogmatic(self):
        x = Opinion(0.7, 0.3, 0.0, 0.5)
        y = Opinion(0.4, 0.6, 0.0, 0.5)
        disj = x | y
        ex, ey = x.expectation(), y.expectation()
        assert disj.expectation() == approx(ex + ey - ex * ey)

    def test_inclusion_exclusion_high_evidence(self):
        x = from_probability(0.75, 1000)
        y = from_probability(0.60, 1000)
        disj = x | y
        ex, ey = x.expectation(), y.expectation()
        assert disj.expectation() == approx(ex + ey - ex * ey, abs=0.01)

    def test_disjunction_produces_valid_opinion(self):
        x = Opinion(0.6, 0.1, 0.3, 0.5)
        y = Opinion(0.4, 0.2, 0.4, 0.5)
        disj = x | y
        assert disj.b + disj.d + disj.u == approx(1.0)
        assert 0.0 <= disj.expectation() <= 1.0


# --- 6. Consensus is commutative ---

class TestConsensusCommutative:
    def test_commutative(self):
        a = Opinion(0.3, 0.2, 0.5, 0.5)
        b = Opinion(0.4, 0.1, 0.5, 0.5)
        ab = consensus_pair(a, b)
        ba = consensus_pair(b, a)
        assert ab == ba

    def test_commutative_different_base_rates(self):
        a = Opinion(0.2, 0.3, 0.5, 0.6)
        b = Opinion(0.5, 0.1, 0.4, 0.3)
        ab = consensus_pair(a, b)
        ba = consensus_pair(b, a)
        assert ab.b == approx(ba.b)
        assert ab.d == approx(ba.d)
        assert ab.u == approx(ba.u)


# --- 7. Consensus is associative ---

class TestConsensusAssociative:
    def test_associative(self):
        a = Opinion(0.3, 0.2, 0.5, 0.5)
        b = Opinion(0.4, 0.1, 0.5, 0.5)
        c = Opinion(0.2, 0.3, 0.5, 0.5)
        ab_c = consensus_pair(consensus_pair(a, b), c)
        a_bc = consensus_pair(a, consensus_pair(b, c))
        assert ab_c.b == approx(a_bc.b)
        assert ab_c.d == approx(a_bc.d)
        assert ab_c.u == approx(a_bc.u)

    def test_associative_via_fold(self):
        ops = [
            Opinion(0.3, 0.2, 0.5, 0.5),
            Opinion(0.4, 0.1, 0.5, 0.5),
            Opinion(0.2, 0.3, 0.5, 0.5),
        ]
        result = consensus(*ops)
        manual = consensus_pair(consensus_pair(ops[0], ops[1]), ops[2])
        assert result.b == approx(manual.b)
        assert result.d == approx(manual.d)
        assert result.u == approx(manual.u)


# --- 8. Consensus reduces uncertainty ---

class TestConsensusReducesUncertainty:
    def test_uncertainty_decreases(self):
        a = Opinion(0.3, 0.2, 0.5, 0.5)
        b = Opinion(0.4, 0.1, 0.5, 0.5)
        fused = consensus_pair(a, b)
        assert fused.u <= min(a.u, b.u) + 1e-9

    def test_uncertainty_decreases_asymmetric(self):
        a = Opinion(0.1, 0.1, 0.8, 0.5)
        b = Opinion(0.6, 0.1, 0.3, 0.5)
        fused = consensus_pair(a, b)
        assert fused.u <= min(a.u, b.u) + 1e-9


# --- 9. Discounting with vacuous trust produces vacuous opinion ---

class TestDiscountVacuousTrust:
    def test_vacuous_trust(self):
        trust = Opinion.vacuous()
        source = Opinion(0.7, 0.1, 0.2, 0.6)
        result = discount(trust, source)
        assert result.b == approx(0.0)
        assert result.d == approx(0.0)
        assert result.u == approx(1.0)

    def test_vacuous_trust_preserves_base_rate(self):
        trust = Opinion.vacuous()
        source = Opinion(0.7, 0.1, 0.2, 0.6)
        result = discount(trust, source)
        assert result.a == approx(source.a)


# --- 10. Discounting preserves base rate ---

class TestDiscountPreservesBaseRate:
    def test_base_rate_preserved(self):
        trust = Opinion(0.8, 0.1, 0.1, 0.5)
        source = Opinion(0.5, 0.2, 0.3, 0.7)
        result = discount(trust, source)
        assert result.a == approx(source.a)


# --- 11. Negation is involution ---

class TestNegationInvolution:
    def test_double_negation(self):
        o = Opinion(0.3, 0.2, 0.5, 0.6)
        assert ~~o == o

    def test_double_negation_vacuous(self):
        o = Opinion.vacuous()
        assert ~~o == o

    def test_negation_swaps_b_d(self):
        o = Opinion(0.3, 0.2, 0.5, 0.6)
        neg = ~o
        assert neg.b == approx(o.d)
        assert neg.d == approx(o.b)
        assert neg.u == approx(o.u)
        assert neg.a == approx(1.0 - o.a)


# --- 12. Round-trip Opinion -> BetaEvidence -> Opinion ---

class TestRoundTrip:
    def test_roundtrip(self):
        o = Opinion(0.3, 0.2, 0.5, 0.6)
        rt = o.to_beta_evidence().to_opinion()
        assert rt.b == approx(o.b)
        assert rt.d == approx(o.d)
        assert rt.u == approx(o.u)
        assert rt.a == approx(o.a)

    def test_roundtrip_vacuous(self):
        o = Opinion.vacuous(a=0.7)
        rt = o.to_beta_evidence().to_opinion()
        assert rt == o

    def test_dogmatic_raises(self):
        with pytest.raises(ValueError, match="dogmatic"):
            Opinion.dogmatic_true().to_beta_evidence()


# --- 13. from_evidence(0, 0) produces vacuous opinion ---

class TestFromEvidenceVacuous:
    def test_zero_evidence(self):
        o = from_evidence(0, 0)
        assert o.b == approx(0.0)
        assert o.d == approx(0.0)
        assert o.u == approx(1.0)


# --- 14. from_probability(0.5, 0) produces vacuous opinion ---

class TestFromProbabilityVacuous:
    def test_zero_sample_size(self):
        o = from_probability(0.5, 0)
        assert o.b == approx(0.0)
        assert o.d == approx(0.0)
        assert o.u == approx(1.0)


# --- 15. from_probability(0.7, 100) produces narrow opinion near 0.7 ---

class TestFromProbabilityNarrow:
    def test_narrow_opinion(self):
        o = from_probability(0.7, 100)
        assert o.expectation() == approx(0.7, abs=0.02)
        # With 100 observations, uncertainty should be small
        assert o.u < 0.05

    def test_evidence_counts(self):
        o = from_probability(0.7, 100)
        be = o.to_beta_evidence()
        assert be.r == approx(70.0)
        assert be.s == approx(30.0)


# --- Additional edge-case tests ---

class TestConsensusErrors:
    def test_two_dogmatic_raises(self):
        with pytest.raises(ValueError, match="dogmatic"):
            consensus_pair(Opinion.dogmatic_true(), Opinion.dogmatic_false())

    def test_single_opinion_consensus(self):
        o = Opinion(0.3, 0.2, 0.5, 0.5)
        assert consensus(o) == o

    def test_empty_consensus_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            consensus()


class TestBetaEvidenceValidation:
    def test_negative_r_rejected(self):
        with pytest.raises(ValueError):
            BetaEvidence(-1, 0)

    def test_negative_s_rejected(self):
        with pytest.raises(ValueError):
            BetaEvidence(0, -1)


class TestUncertaintyInterval:
    def test_vacuous(self):
        o = Opinion.vacuous()
        lo, hi = o.uncertainty_interval()
        assert lo == approx(0.0)
        assert hi == approx(1.0)

    def test_dogmatic_true(self):
        o = Opinion.dogmatic_true()
        lo, hi = o.uncertainty_interval()
        assert lo == approx(1.0)
        assert hi == approx(1.0)


# ── Hypothesis strategies for opinions ─────────────────────────────


@st.composite
def valid_opinions(draw, min_uncertainty=0.01):
    """Generate random valid opinions with u > 0.

    Opinions with u=0 are dogmatic and cannot be fused via consensus
    (raises ValueError).  The min_uncertainty bound ensures fusibility.
    """
    # Draw b, d, u such that b + d + u = 1, all >= 0, u >= min_uncertainty
    u = draw(st.floats(min_value=min_uncertainty, max_value=1.0 - 1e-6))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    # Clamp to avoid floating-point drift
    d = max(0.0, d)
    # Base rate in (0, 1)
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    assume(abs(b + d + u - 1.0) < 1e-9)
    assume(b >= 0.0 and d >= 0.0 and u >= 0.0)
    return Opinion(b, d, u, a)


# ── F29: Property tests for consensus algebra ──────────────────────


class TestConsensusPropertyTests:
    """Hypothesis property tests for consensus fusion (F29).

    These fill coverage gaps from audit-opinion-algebra GAP 1:
    commutativity and vacuous identity were only tested with
    concrete examples, not with randomized inputs.
    """

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=100, deadline=None)
    def test_commutativity(self, op_a, op_b):
        """fuse(a, b) == fuse(b, a) — Jøsang Theorem 7 is symmetric.

        The consensus operator must be commutative for all valid
        non-dogmatic opinion pairs.
        """
        ab = consensus_pair(op_a, op_b)
        ba = consensus_pair(op_b, op_a)
        assert math.isclose(ab.b, ba.b, abs_tol=1e-9), (
            f"b mismatch: {ab.b} vs {ba.b}"
        )
        assert math.isclose(ab.d, ba.d, abs_tol=1e-9), (
            f"d mismatch: {ab.d} vs {ba.d}"
        )
        assert math.isclose(ab.u, ba.u, abs_tol=1e-9), (
            f"u mismatch: {ab.u} vs {ba.u}"
        )
        assert math.isclose(ab.a, ba.a, abs_tol=1e-9), (
            f"a mismatch: {ab.a} vs {ba.a}"
        )

    @given(valid_opinions())
    @settings(max_examples=100, deadline=None)
    def test_vacuous_identity(self, op):
        """fuse(a, vacuous) ≈ a — vacuous opinion is the identity element.

        Per Jøsang 2001 Theorem 7: fusing with (0, 0, 1, a_v) should
        return the original opinion unchanged (for b, d, u components).
        The base rate of the result equals the original's base rate
        when the other operand is vacuous (verified algebraically in
        audit-opinion-algebra Finding 15).
        """
        vacuous = Opinion.vacuous(a=op.a)  # match base rate to avoid denom_a edge case
        fused = consensus_pair(op, vacuous)
        assert math.isclose(fused.b, op.b, abs_tol=1e-9), (
            f"b: fused={fused.b}, original={op.b}"
        )
        assert math.isclose(fused.d, op.d, abs_tol=1e-9), (
            f"d: fused={fused.d}, original={op.d}"
        )
        assert math.isclose(fused.u, op.u, abs_tol=1e-9), (
            f"u: fused={fused.u}, original={op.u}"
        )
        assert math.isclose(fused.a, op.a, abs_tol=1e-9), (
            f"a: fused={fused.a}, original={op.a}"
        )

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=100, deadline=None)
    def test_consensus_reduces_uncertainty(self, op_a, op_b):
        """Consensus never increases uncertainty (Josang 2001, p.25-26).

        For any two non-dogmatic opinions, the fused uncertainty must be
        <= min(a.u, b.u). This is a guard test to maintain the invariant.

        Phase 1 Red: this property must hold for the consensus operator
        to be valid for fusing corpus and categorical opinions.
        """
        fused = consensus_pair(op_a, op_b)
        assert fused.u <= min(op_a.u, op_b.u) + 1e-9, (
            f"Consensus increased uncertainty: fused.u={fused.u}, "
            f"min(a.u={op_a.u}, b.u={op_b.u})={min(op_a.u, op_b.u)}"
        )

    @given(valid_opinions())
    @settings(max_examples=100, deadline=None)
    def test_vacuous_identity_different_base_rate(self, op):
        """fuse(a, vacuous_with_different_a) still preserves b, d, u of a.

        The base rate of the result should equal op.a per the consensus
        formula derivation (audit-opinion-algebra Finding 15 verified this
        algebraically for the non-vacuous case).
        """
        # Use a different base rate for vacuous
        vac_a = 1.0 - op.a  # guaranteed different and in (0, 1)
        assume(0.01 < vac_a < 0.99)
        vacuous = Opinion.vacuous(a=vac_a)
        fused = consensus_pair(op, vacuous)
        # b, d, u should be preserved regardless of vacuous base rate
        assert math.isclose(fused.b, op.b, abs_tol=1e-9), (
            f"b: fused={fused.b}, original={op.b}"
        )
        assert math.isclose(fused.d, op.d, abs_tol=1e-9), (
            f"d: fused={fused.d}, original={op.d}"
        )
        assert math.isclose(fused.u, op.u, abs_tol=1e-9), (
            f"u: fused={fused.u}, original={op.u}"
        )
        # Base rate should be original's base rate (vacuous contributes no information)
        assert math.isclose(fused.a, op.a, abs_tol=1e-9), (
            f"a: fused={fused.a}, original={op.a}"
        )


# ── Uncertainty Maximization (Jøsang 2001 Def 16, p.30) ─────────


class TestUncertaintyMaximization:
    """Jøsang 2001 p.30: maximize u while preserving E(x)."""

    def test_concrete_example(self):
        op = Opinion(0.7, 0.1, 0.2, 0.5)
        result = op.maximize_uncertainty()
        assert abs(result.expectation() - op.expectation()) < 1e-9
        assert result.uncertainty >= op.uncertainty

    def test_vacuous_unchanged(self):
        op = Opinion.vacuous(0.5)
        result = op.maximize_uncertainty()
        assert abs(result.uncertainty - 1.0) < 1e-9

    def test_dogmatic_true(self):
        op = Opinion(1.0, 0.0, 0.0, 0.5)
        result = op.maximize_uncertainty()
        # E = 1.0, u_max = min(1/0.5, 0/0.5) = min(2, 0) = 0
        # Can't increase uncertainty when E=1
        assert abs(result.uncertainty - 0.0) < 1e-9

    def test_dogmatic_false(self):
        op = Opinion(0.0, 1.0, 0.0, 0.5)
        result = op.maximize_uncertainty()
        # E = 0.0, u_max = min(0/0.5, 1/0.5) = min(0, 2) = 0
        # Can't increase uncertainty when E=0
        assert abs(result.uncertainty - 0.0) < 1e-9

    def test_b_becomes_zero_case(self):
        """When E/a <= (1-E)/(1-a), b should become 0."""
        op = Opinion(0.2, 0.6, 0.2, 0.5)
        # E = 0.2 + 0.5*0.2 = 0.3
        # E/a = 0.6, (1-E)/(1-a) = 0.7/0.5 = 1.4
        # u_max = 0.6, b = 0, d = 1 - 0.6 = 0.4
        result = op.maximize_uncertainty()
        assert abs(result.b) < 1e-9
        assert abs(result.expectation() - op.expectation()) < 1e-9

    def test_d_becomes_zero_case(self):
        """When (1-E)/(1-a) < E/a, d should become 0."""
        op = Opinion(0.7, 0.1, 0.2, 0.5)
        # E = 0.7 + 0.5*0.2 = 0.8
        # E/a = 1.6, (1-E)/(1-a) = 0.2/0.5 = 0.4
        # u_max = 0.4, d = 0, b = 0.8 - 0.5*0.4 = 0.6
        result = op.maximize_uncertainty()
        assert abs(result.d) < 1e-9
        assert abs(result.expectation() - op.expectation()) < 1e-9

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_preserves_expectation(self, op):
        result = op.maximize_uncertainty()
        assert abs(result.expectation() - op.expectation()) < 1e-9

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_uncertainty_never_decreases(self, op):
        result = op.maximize_uncertainty()
        assert result.uncertainty >= op.uncertainty - 1e-9

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_idempotent(self, op):
        """Maximizing twice should give same result as once."""
        once = op.maximize_uncertainty()
        twice = once.maximize_uncertainty()
        assert abs(twice.b - once.b) < 1e-9
        assert abs(twice.d - once.d) < 1e-9
        assert abs(twice.u - once.u) < 1e-9


# ── Opinion Ordering (Jøsang 2001 Def 10, p.9) ─────────────────


class TestOpinionOrdering:
    """Jøsang 2001 Def 10, p.9: opinion ordering by E(x), then u, then a."""

    def test_higher_expectation_is_greater(self):
        high = Opinion(0.8, 0.1, 0.1, 0.5)  # E = 0.85
        low = Opinion(0.3, 0.5, 0.2, 0.5)   # E = 0.4
        assert high > low

    def test_same_expectation_less_uncertainty_is_greater(self):
        # E = 0.8 for both
        certain = Opinion(0.8, 0.2, 0.0, 0.5)    # E = 0.8, u = 0
        uncertain = Opinion(0.3, 0.0, 0.7, 5/7)   # E = 0.3 + 5/7*0.7 = 0.8, u = 0.7
        assert certain > uncertain

    def test_same_e_same_u_less_a_is_greater(self):
        # Same E and u, different a
        # b + a*u = E, b + d + u = 1
        # Pick u=0.4, E=0.5
        # a=0.25: b = 0.5 - 0.25*0.4 = 0.4, d = 0.2
        # a=0.75: b = 0.5 - 0.75*0.4 = 0.2, d = 0.4
        low_a = Opinion(0.4, 0.2, 0.4, 0.25)   # E=0.5, u=0.4, a=0.25
        high_a = Opinion(0.2, 0.4, 0.4, 0.75)  # E=0.5, u=0.4, a=0.75
        assert low_a > high_a

    def test_equality(self):
        a = Opinion(0.3, 0.2, 0.5, 0.5)
        b = Opinion(0.3, 0.2, 0.5, 0.5)
        assert a <= b
        assert a >= b
        assert not (a < b)
        assert not (a > b)

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_total_ordering(self, a, b):
        """Ordering is total: either a <= b or b <= a."""
        assert (a <= b) or (b <= a)

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_reflexive(self, a):
        assert a <= a


# ── Phase 8B: Additional Hypothesis property tests ───────────────


class TestConsensusAssociativityProperty:
    """Hypothesis property test for consensus associativity."""

    @given(valid_opinions(), valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_consensus_associative(self, a, b, c):
        """consensus(a, consensus(b, c)) ≈ consensus(consensus(a, b), c)"""
        # Skip when any pair would be two dogmatic opinions (u=0 for both)
        # because consensus is undefined for that case
        # (valid_opinions strategy already ensures u >= 0.01, but guard anyway)
        assume(a.u > 1e-6 and b.u > 1e-6 and c.u > 1e-6)
        ab_c = consensus_pair(consensus_pair(a, b), c)
        a_bc = consensus_pair(a, consensus_pair(b, c))
        assert abs(ab_c.b - a_bc.b) < 1e-6, f"b: {ab_c.b} vs {a_bc.b}"
        assert abs(ab_c.d - a_bc.d) < 1e-6, f"d: {ab_c.d} vs {a_bc.d}"
        assert abs(ab_c.u - a_bc.u) < 1e-6, f"u: {ab_c.u} vs {a_bc.u}"


class TestConjunctionPreservesSum:
    """Conjunction must preserve b + d + u = 1."""

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_conjunction_preserves_sum(self, a, b):
        result = a & b
        assert abs(result.b + result.d + result.u - 1.0) < 1e-9


class TestDisjunctionPreservesSum:
    """Disjunction must preserve b + d + u = 1."""

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_disjunction_preserves_sum(self, a, b):
        result = a | b
        assert abs(result.b + result.d + result.u - 1.0) < 1e-9


class TestNegationInvolutionProperty:
    """Negation involution: ~~op ≈ op for all valid opinions."""

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_negation_involution(self, op):
        """~~op ≈ op"""
        result = ~~op
        assert abs(result.b - op.b) < 1e-9
        assert abs(result.d - op.d) < 1e-9
        assert abs(result.u - op.u) < 1e-9
        assert abs(result.a - op.a) < 1e-9


class TestBetaEvidenceRoundTripProperty:
    """Round-trip Opinion -> BetaEvidence -> Opinion for non-dogmatic opinions."""

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_beta_evidence_round_trip(self, op):
        """op.to_beta_evidence().to_opinion() ≈ op (when u > 0)"""
        assume(op.u > 1e-6)  # dogmatic opinions can't round-trip
        evidence = op.to_beta_evidence()
        restored = evidence.to_opinion()
        assert abs(restored.b - op.b) < 1e-6
        assert abs(restored.d - op.d) < 1e-6
        assert abs(restored.u - op.u) < 1e-6


class TestDiscountVacuousTrustProperty:
    """Discounting with vacuous trust yields vacuous result."""

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_discount_vacuous_trust_yields_vacuous(self, op):
        """Discounting with vacuous trust yields vacuous result."""
        vacuous_trust = Opinion.vacuous(0.5)
        result = discount(vacuous_trust, op)
        assert abs(result.u - 1.0) < 1e-9


# ── WBF tests (van der Heijden 2018 Definition 4) ───────────────────


class TestWBF:
    """Weighted Belief Fusion — N-source generalization of consensus."""

    def test_wbf_single_opinion(self):
        """WBF of a single opinion returns it unchanged."""
        op = Opinion(0.3, 0.2, 0.5, 0.6)
        result = wbf(op)
        assert result == op

    def test_wbf_empty_raises(self):
        """WBF with no opinions raises ValueError."""
        with pytest.raises(ValueError):
            wbf()

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_two_equals_consensus_pair(self, a, b):
        """For N=2 non-dogmatic opinions, WBF == consensus_pair."""
        result_wbf = wbf(a, b)
        result_cp = consensus_pair(a, b)
        assert abs(result_wbf.b - result_cp.b) < 1e-6
        assert abs(result_wbf.d - result_cp.d) < 1e-6
        assert abs(result_wbf.u - result_cp.u) < 1e-6
        assert abs(result_wbf.a - result_cp.a) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_commutativity(self, a, b):
        """WBF(a, b) == WBF(b, a)."""
        r1 = wbf(a, b)
        r2 = wbf(b, a)
        assert abs(r1.b - r2.b) < 1e-6
        assert abs(r1.d - r2.d) < 1e-6
        assert abs(r1.u - r2.u) < 1e-6
        assert abs(r1.a - r2.a) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_vacuous_identity(self, a):
        """WBF(a, vacuous) == a — vacuous contributes nothing."""
        vacuous = Opinion.vacuous(a.a)
        result = wbf(a, vacuous)
        assert abs(result.b - a.b) < 1e-6
        assert abs(result.d - a.d) < 1e-6
        assert abs(result.u - a.u) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_uncertainty_reduction(self, a, b):
        """Fusing two opinions never increases uncertainty beyond the minimum."""
        result = wbf(a, b)
        assert result.u <= min(a.u, b.u) + _TOL

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_sum_invariant(self, a, b):
        """b + d + u == 1 for fused result."""
        result = wbf(a, b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_expectation_valid(self, a, b):
        """Fused expectation is in [0, 1].

        Note: E(wbf(a,b)) is NOT necessarily between E(a) and E(b) because
        fusion concentrates belief mass, reducing uncertainty and shifting
        the expectation. This is correct behavior per Jøsang Theorem 7.
        """
        result = wbf(a, b)
        assert -_TOL <= result.expectation() <= 1.0 + _TOL

    def test_wbf_dogmatic_raises(self):
        """WBF raises when given a dogmatic opinion."""
        dogmatic = Opinion.dogmatic_true()
        normal = Opinion(0.3, 0.2, 0.5, 0.5)
        with pytest.raises(ValueError, match="dogmatic"):
            wbf(dogmatic, normal)

    def test_wbf_three_sources(self):
        """Concrete 3-source WBF: result is valid and uncertainty decreases."""
        a = Opinion(0.5, 0.1, 0.4, 0.5)
        b = Opinion(0.3, 0.3, 0.4, 0.5)
        c = Opinion(0.6, 0.2, 0.2, 0.5)
        result = wbf(a, b, c)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6
        assert result.u < min(a.u, b.u, c.u) + _TOL
        assert result.b >= 0.0
        assert result.d >= 0.0
        assert result.u >= 0.0


# ── CCF tests (van der Heijden 2018 Definition 5) ───────────────────


class TestCCF:
    """Cumulative & Compromise Fusion — handles dogmatic sources."""

    def test_ccf_single_opinion(self):
        """CCF of a single opinion returns it unchanged."""
        op = Opinion(0.3, 0.2, 0.5, 0.6)
        result = ccf(op)
        assert result == op

    def test_ccf_empty_raises(self):
        """CCF with no opinions raises ValueError."""
        with pytest.raises(ValueError):
            ccf()

    def test_ccf_handles_dogmatic(self):
        """CCF can fuse two dogmatic opinions without raising."""
        dt = Opinion.dogmatic_true()
        df = Opinion.dogmatic_false()
        result = ccf(dt, df)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_ccf_all_dogmatic_same(self):
        """CCF of identical dogmatic opinions returns the same opinion."""
        dt = Opinion.dogmatic_true()
        result = ccf(dt, dt)
        assert abs(result.b - 1.0) < 1e-6
        assert abs(result.d - 0.0) < 1e-6
        assert abs(result.u - 0.0) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_ccf_sum_invariant(self, a, b):
        """b + d + u == 1 for CCF result."""
        result = ccf(a, b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6


# ── CCF Definition 5 tests (van der Heijden 2018) ───────────────────


class TestCCFDefinition5:
    """CCF matches van der Heijden 2018 Definition 5 three-phase process."""

    def test_all_dogmatic_agreeing(self):
        """Two identical dogmatic opinions should fuse to the same opinion."""
        a = Opinion.dogmatic_true(0.5)
        result = ccf(a, a)
        assert result.b == pytest.approx(1.0, abs=1e-6)
        assert result.d == pytest.approx(0.0, abs=1e-6)
        assert result.u == pytest.approx(0.0, abs=1e-6)

    def test_all_dogmatic_disagreeing(self):
        """CCF of dogmatic_true and dogmatic_false: consensus at midpoint.

        Consensus: min(1,0)=0 for b, min(0,1)=0 for d
        Residuals: (1,0) and (0,1), average = (0.5, 0.5)
        Combined: b=0.5, d=0.5, u=0
        """
        a = Opinion.dogmatic_true(0.5)
        b = Opinion.dogmatic_false(0.5)
        result = ccf(a, b)
        assert result.b == pytest.approx(0.5, abs=1e-6)
        assert result.d == pytest.approx(0.5, abs=1e-6)
        assert result.u == pytest.approx(0.0, abs=1e-6)

    def test_all_dogmatic_three_sources(self):
        """Three dogmatic: two true, one false.

        Consensus b: min(1,1,0)=0; consensus d: min(0,0,1)=0
        Residual b: [1,1,0], mean=2/3; residual d: [0,0,1], mean=1/3
        Combined: b=2/3, d=1/3, u=0
        """
        dt = Opinion.dogmatic_true(0.5)
        df = Opinion.dogmatic_false(0.5)
        result = ccf(dt, dt, df)
        assert result.b == pytest.approx(2.0 / 3.0, abs=1e-6)
        assert result.d == pytest.approx(1.0 / 3.0, abs=1e-6)
        assert result.u == pytest.approx(0.0, abs=1e-6)

    def test_mixed_dogmatic_nondogmatic(self):
        """Mixed case: CCF should NOT just average WBF result with dogmatic.

        Dogmatic: b=1, d=0, u=0
        Uncertain: b=0.4, d=0.2, u=0.4

        Consensus b: min(1, 0.4) = 0.4; consensus d: min(0, 0.2) = 0.0
        Residual b: [0.6, 0.0], mean=0.3; residual d: [0.0, 0.2], mean=0.1
        Raw: b=0.7, d=0.1, u_avg=mean(0, 0.4)=0.2
        Sum=1.0, no normalization needed.
        """
        dogmatic = Opinion.dogmatic_true(0.5)
        uncertain = Opinion(0.4, 0.2, 0.4, 0.5)
        result = ccf(dogmatic, uncertain)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6
        assert result.b == pytest.approx(0.7, abs=1e-6)
        assert result.d == pytest.approx(0.1, abs=1e-6)
        assert result.u == pytest.approx(0.2, abs=1e-6)

    def test_three_sources_mixed(self):
        """Three sources: two dogmatic, one uncertain."""
        d1 = Opinion.dogmatic_true(0.5)
        d2 = Opinion.dogmatic_false(0.5)
        u1 = Opinion(0.3, 0.3, 0.4, 0.5)
        result = ccf(d1, d2, u1)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    def test_nondogmatic_delegates_to_wbf(self):
        """Two non-dogmatic opinions: CCF delegates to WBF.

        WBF weights by certainty (1/u_i), producing the same result as
        consensus_pair for N=2.
        """
        a = Opinion(0.6, 0.1, 0.3, 0.5)
        b = Opinion(0.2, 0.5, 0.3, 0.5)
        result = ccf(a, b)
        expected = wbf(a, b)
        assert result.b == pytest.approx(expected.b, abs=1e-6)
        assert result.d == pytest.approx(expected.d, abs=1e-6)
        assert result.u == pytest.approx(expected.u, abs=1e-6)


class TestCCFProperties:
    """CCF properties from van der Heijden 2018."""

    @given(a=valid_opinions(), b=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_commutativity(self, a, b):
        """CCF(a, b) == CCF(b, a)."""
        r1 = ccf(a, b)
        r2 = ccf(b, a)
        assert abs(r1.b - r2.b) < 1e-6
        assert abs(r1.d - r2.d) < 1e-6
        assert abs(r1.u - r2.u) < 1e-6

    @given(a=valid_opinions(), b=valid_opinions(), c=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_commutativity_three(self, a, b, c):
        """CCF(a, b, c) is the same regardless of argument order."""
        result_abc = ccf(a, b, c)
        result_bca = ccf(b, c, a)
        result_cab = ccf(c, a, b)
        assert abs(result_abc.b - result_bca.b) < 1e-6
        assert abs(result_abc.b - result_cab.b) < 1e-6
        assert abs(result_abc.d - result_bca.d) < 1e-6
        assert abs(result_abc.d - result_cab.d) < 1e-6

    @given(a=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_single_identity(self, a):
        """CCF of a single opinion is itself."""
        result = ccf(a)
        assert result == a

    @given(a=valid_opinions(), b=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_sum_invariant_property(self, a, b):
        """Fused opinion satisfies b + d + u = 1."""
        result = ccf(a, b)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    @given(a=valid_opinions(), b=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_non_negative(self, a, b):
        """Fused opinion has non-negative components."""
        result = ccf(a, b)
        assert result.b >= -1e-9
        assert result.d >= -1e-9
        assert result.u >= -1e-9

    @given(a=valid_opinions(min_uncertainty=0.05), b=valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_ccf_nondogmatic_matches_wbf(self, a, b):
        """For non-dogmatic inputs, CCF delegates to WBF exactly.

        The expectation-between-inputs property does NOT hold for WBF-based
        CCF because WBF concentrates evidence (reduces u), shifting E toward
        b/(b+d). This is correct evidence-accumulation behavior.
        """
        result_ccf = ccf(a, b)
        result_wbf = wbf(a, b)
        assert abs(result_ccf.b - result_wbf.b) < 1e-9
        assert abs(result_ccf.d - result_wbf.d) < 1e-9
        assert abs(result_ccf.u - result_wbf.u) < 1e-9


# ── Fuse dispatcher tests ───────────────────────────────────────────


class TestFuse:
    """fuse() dispatcher: auto selects WBF or CCF."""

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_fuse_auto_selects_wbf(self, a, b):
        """For non-dogmatic inputs, fuse(auto) == wbf()."""
        result_fuse = fuse(a, b, method="auto")
        result_wbf = wbf(a, b)
        assert abs(result_fuse.b - result_wbf.b) < 1e-9
        assert abs(result_fuse.d - result_wbf.d) < 1e-9
        assert abs(result_fuse.u - result_wbf.u) < 1e-9

    def test_fuse_auto_falls_back_to_ccf(self):
        """For dogmatic inputs, fuse(auto) doesn't raise."""
        dt = Opinion.dogmatic_true()
        df = Opinion.dogmatic_false()
        result = fuse(dt, df, method="auto")
        assert abs(result.b + result.d + result.u - 1.0) < 1e-6

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_fuse_explicit_wbf(self, a, b):
        """fuse(method='wbf') == wbf()."""
        r1 = fuse(a, b, method="wbf")
        r2 = wbf(a, b)
        assert abs(r1.b - r2.b) < 1e-9
        assert abs(r1.d - r2.d) < 1e-9

    @given(valid_opinions(min_uncertainty=0.05), valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_fuse_explicit_ccf(self, a, b):
        """fuse(method='ccf') == ccf()."""
        r1 = fuse(a, b, method="ccf")
        r2 = ccf(a, b)
        assert abs(r1.b - r2.b) < 1e-9
        assert abs(r1.d - r2.d) < 1e-9


# ── Additional fusion property tests (audit-2026-03-28 gaps) ──────


class TestWBFAdditionalProperties:
    """WBF properties identified as missing in audit-2026-03-28."""

    @given(
        valid_opinions(min_uncertainty=0.05),
        valid_opinions(min_uncertainty=0.05),
        valid_opinions(min_uncertainty=0.05),
    )
    @settings(max_examples=200, deadline=None)
    def test_wbf_three_source_commutativity(self, a, b, c):
        """WBF(a, b, c) is the same regardless of argument order.

        Jøsang Theorem 7 generalizes to N sources — the multi-source
        formula uses symmetric sums so order should not matter.
        """
        r_abc = wbf(a, b, c)
        r_bca = wbf(b, c, a)
        r_cab = wbf(c, a, b)
        assert abs(r_abc.b - r_bca.b) < 1e-6, f"b: {r_abc.b} vs {r_bca.b}"
        assert abs(r_abc.b - r_cab.b) < 1e-6, f"b: {r_abc.b} vs {r_cab.b}"
        assert abs(r_abc.d - r_bca.d) < 1e-6, f"d: {r_abc.d} vs {r_bca.d}"
        assert abs(r_abc.d - r_cab.d) < 1e-6, f"d: {r_abc.d} vs {r_cab.d}"
        assert abs(r_abc.u - r_bca.u) < 1e-6, f"u: {r_abc.u} vs {r_bca.u}"
        assert abs(r_abc.u - r_cab.u) < 1e-6, f"u: {r_abc.u} vs {r_cab.u}"

    @given(valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_self_fusion_preserves_belief_disbelief_ratio(self, a):
        """When fusing identical opinions, the b:d ratio is preserved.

        WBF self-fusion concentrates belief mass (reduces u) while
        maintaining the relative proportion of b and d. Expectation
        is NOT preserved in general because E = b + a*u and u shrinks.
        """
        assume(a.b + a.d > 1e-6)  # skip near-vacuous
        result = wbf(a, a)
        # b/d ratio should be preserved
        if a.b > 1e-9 and a.d > 1e-9:
            orig_ratio = a.b / a.d
            result_ratio = result.b / result.d
            assert abs(orig_ratio - result_ratio) < 1e-4, (
                f"b:d ratio changed: {orig_ratio} -> {result_ratio}"
            )

    @given(valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_self_fusion_reduces_uncertainty(self, a):
        """Fusing an opinion with itself concentrates belief: u decreases."""
        result = wbf(a, a)
        assert result.u <= a.u + _TOL

    @given(valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_wbf_base_rate_clamping_observable(self, a):
        """Document that WBF clamps base rates to [0.01, 0.99].

        This is a known deviation from Jøsang 2001 (audit-2026-03-28 bug #2).
        The test documents the current behavior so any future fix is visible.
        """
        result = wbf(a, a)
        assert result.a >= 0.01, f"Base rate below clamp: {result.a}"
        assert result.a <= 0.99, f"Base rate above clamp: {result.a}"


class TestCCFAdditionalProperties:
    """CCF properties identified as missing in audit-2026-03-28."""

    @given(
        a=valid_opinions(),
        b=valid_opinions(),
        c=valid_opinions(),
    )
    @settings(max_examples=100, deadline=None)
    def test_ccf_associativity(self, a, b, c):
        """CCF(CCF(a, b), c) ≈ CCF(a, CCF(b, c)).

        Non-dogmatic CCF delegates to WBF which is associative via
        consensus_pair folding. Dogmatic CCF uses min+average which is
        associative by construction (min and mean are both associative).
        """
        ab_c = ccf(ccf(a, b), c)
        a_bc = ccf(a, ccf(b, c))
        assert abs(ab_c.b - a_bc.b) < 1e-6, (
            f"CCF not associative — b: {ab_c.b} vs {a_bc.b}, "
            f"delta={abs(ab_c.b - a_bc.b)}"
        )
        assert abs(ab_c.d - a_bc.d) < 1e-6, (
            f"CCF not associative — d: {ab_c.d} vs {a_bc.d}, "
            f"delta={abs(ab_c.d - a_bc.d)}"
        )
        assert abs(ab_c.u - a_bc.u) < 1e-6, (
            f"CCF not associative — u: {ab_c.u} vs {a_bc.u}, "
            f"delta={abs(ab_c.u - a_bc.u)}"
        )

    @given(a=valid_opinions(min_uncertainty=0.05))
    @settings(max_examples=200, deadline=None)
    def test_ccf_self_fusion_preserves_bd_ratio(self, a):
        """CCF(a, a) preserves b:d ratio (inherited from WBF for non-dogmatic).

        WBF concentrates evidence (reduces u), so expectation E = b + a*u
        shifts toward b/(b+d). This is correct evidence-accumulation behavior.
        The b:d ratio IS preserved, matching WBF's self-fusion property.
        """
        assume(a.b + a.d > 1e-6)  # skip near-vacuous
        result = ccf(a, a)
        if a.b > 1e-9 and a.d > 1e-9:
            orig_ratio = a.b / a.d
            result_ratio = result.b / result.d
            assert abs(orig_ratio - result_ratio) < 1e-4, (
                f"b:d ratio changed: {orig_ratio} -> {result_ratio}"
            )

    @given(a=valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_ccf_base_rate_clamping_observable(self, a):
        """Document that CCF clamps base rates to [0.01, 0.99].

        Known deviation from literature (audit-2026-03-28 bug #2).
        """
        result = ccf(a, a)
        assert result.a >= 0.01
        assert result.a <= 0.99


class TestConjunctionDisjunctionDeMorgan:
    """Conjunction/disjunction should satisfy De Morgan's law via negation.

    Per Jøsang 2001: ~(A & B) should equal (~A | ~B) for independent opinions.
    This is a consequence of the dual construction of conjunction/disjunction.
    """

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_de_morgan_conjunction(self, a, b):
        """~(a & b) ≈ (~a | ~b)."""
        lhs = ~(a & b)
        rhs = (~a) | (~b)
        assert abs(lhs.b - rhs.b) < 1e-9, f"b: {lhs.b} vs {rhs.b}"
        assert abs(lhs.d - rhs.d) < 1e-9, f"d: {lhs.d} vs {rhs.d}"
        assert abs(lhs.u - rhs.u) < 1e-9, f"u: {lhs.u} vs {rhs.u}"

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_de_morgan_disjunction(self, a, b):
        """~(a | b) ≈ (~a & ~b)."""
        lhs = ~(a | b)
        rhs = (~a) & (~b)
        assert abs(lhs.b - rhs.b) < 1e-9, f"b: {lhs.b} vs {rhs.b}"
        assert abs(lhs.d - rhs.d) < 1e-9, f"d: {lhs.d} vs {rhs.d}"
        assert abs(lhs.u - rhs.u) < 1e-9, f"u: {lhs.u} vs {rhs.u}"


class TestDiscountProperties:
    """Discount operator properties from Jøsang 2001 Def 14."""

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_discount_preserves_base_rate(self, trust, source):
        """Discounting preserves the source's base rate (Jøsang Def 14)."""
        result = discount(trust, source)
        assert abs(result.a - source.a) < 1e-9

    @given(valid_opinions(), valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_discount_sum_invariant(self, trust, source):
        """Discounted opinion satisfies b + d + u = 1."""
        result = discount(trust, source)
        assert abs(result.b + result.d + result.u - 1.0) < 1e-9

    @given(valid_opinions())
    @settings(max_examples=200, deadline=None)
    def test_discount_full_trust_is_identity(self, source):
        """Discounting with dogmatic trust returns the source unchanged.

        Per Jøsang Def 14: when trust = (1, 0, 0, a), the discount
        formula yields b=1*source.b, d=1*source.d, u=0+0+1*source.u = source.u.
        """
        full_trust = Opinion.dogmatic_true(0.5)
        result = discount(full_trust, source)
        assert abs(result.b - source.b) < 1e-9
        assert abs(result.d - source.d) < 1e-9
        assert abs(result.u - source.u) < 1e-9
