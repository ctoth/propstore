"""Tests for propstore.opinion — Jøsang 2001 subjective logic operations."""

import math

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.opinion import (
    BetaEvidence,
    Opinion,
    consensus,
    consensus_pair,
    discount,
    from_evidence,
    from_probability,
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
