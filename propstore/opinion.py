"""Subjective Logic opinion module — Jøsang 2001.

Implements Opinion and BetaEvidence dataclasses with operators:
negation, conjunction, disjunction, consensus, discounting.

This is a leaf module with ZERO imports from propstore.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Prior weight for non-informative prior (Jøsang p.20)
W = 2

_TOL = 1e-9


@dataclass(frozen=True)
class Opinion:
    """A subjective opinion ω = (b, d, u, a).

    b: belief, d: disbelief, u: uncertainty, a: base rate (atomicity).
    Constraint: b + d + u ≈ 1.0, all in [0,1], a in (0,1).
    """

    b: float
    d: float
    u: float
    a: float = 0.5

    def __post_init__(self) -> None:
        for name, val in [("b", self.b), ("d", self.d), ("u", self.u)]:
            if val < -_TOL or val > 1.0 + _TOL:
                raise ValueError(f"{name}={val} not in [0, 1]")
        if self.a <= 0.0 or self.a >= 1.0:
            raise ValueError(f"a={self.a} not in (0, 1)")
        total = self.b + self.d + self.u
        if abs(total - 1.0) > _TOL:
            raise ValueError(
                f"b + d + u = {total}, expected 1.0"
            )

    # --- Aliases for readability ---

    @property
    def uncertainty(self) -> float:
        """Alias for ``u`` (uncertainty component)."""
        return self.u

    # --- Special constructors ---

    @classmethod
    def vacuous(cls, a: float = 0.5) -> Opinion:
        """Total ignorance."""
        return cls(0.0, 0.0, 1.0, a)

    @classmethod
    def dogmatic_true(cls, a: float = 0.5) -> Opinion:
        """Absolute belief."""
        return cls(1.0, 0.0, 0.0, a)

    @classmethod
    def dogmatic_false(cls, a: float = 0.5) -> Opinion:
        """Absolute disbelief."""
        return cls(0.0, 1.0, 0.0, a)

    # --- Core methods ---

    def expectation(self) -> float:
        """E(ω) = b + a * u  (Jøsang Def 6, p.5)."""
        return self.b + self.a * self.u

    def uncertainty_interval(self) -> tuple[float, float]:
        """[Bel, Pl] = (b, 1 - d)."""
        return (self.b, 1.0 - self.d)

    # --- Conversion ---

    def to_beta_evidence(self) -> BetaEvidence:
        """Opinion -> BetaEvidence (Jøsang Def 12, p.20-21).

        Raises ValueError for dogmatic opinions (u == 0).
        """
        if self.u < _TOL:
            raise ValueError("Cannot convert dogmatic opinion (u≈0) to BetaEvidence")
        r = W * self.b / self.u
        s = W * self.d / self.u
        return BetaEvidence(r, s, self.a)

    # --- Operators ---

    def __invert__(self) -> Opinion:
        """Negation: ~ω = Opinion(d, b, u, 1 - a)  (Jøsang Theorem 6, p.18)."""
        return Opinion(self.d, self.b, self.u, 1.0 - self.a)

    def __and__(self, other: Opinion) -> Opinion:
        """Conjunction (Jøsang Theorem 3, p.14) — independent frames."""
        b = self.b * other.b
        d = self.d + other.d - self.d * other.d
        u = self.b * other.u + self.u * other.b + self.u * other.u
        a = self.a * other.a
        return Opinion(b, d, u, a)

    def __or__(self, other: Opinion) -> Opinion:
        """Disjunction (Jøsang Theorem 4, p.14-15) — independent frames."""
        b = self.b + other.b - self.b * other.b
        d = self.d * other.d
        u = self.d * other.u + self.u * other.d + self.u * other.u
        a = self.a + other.a - self.a * other.a
        return Opinion(b, d, u, a)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return (
            abs(self.b - other.b) < _TOL
            and abs(self.d - other.d) < _TOL
            and abs(self.u - other.u) < _TOL
            and abs(self.a - other.a) < _TOL
        )

    def __hash__(self) -> int:
        return hash((round(self.b, 8), round(self.d, 8), round(self.u, 8), round(self.a, 8)))


@dataclass(frozen=True)
class BetaEvidence:
    """Beta evidence representation: r positive, s negative evidence counts.

    r >= 0, s >= 0, a in (0, 1).
    """

    r: float
    s: float
    a: float = 0.5

    def __post_init__(self) -> None:
        if self.r < 0:
            raise ValueError(f"r={self.r} must be >= 0")
        if self.s < 0:
            raise ValueError(f"s={self.s} must be >= 0")
        if self.a <= 0.0 or self.a >= 1.0:
            raise ValueError(f"a={self.a} not in (0, 1)")

    def to_opinion(self) -> Opinion:
        """BetaEvidence -> Opinion."""
        denom = self.r + self.s + W
        b = self.r / denom
        d = self.s / denom
        u = W / denom
        return Opinion(b, d, u, self.a)


# --- Module-level convenience functions ---


def from_evidence(r: float, s: float, a: float = 0.5) -> Opinion:
    """Create opinion from evidence counts."""
    return BetaEvidence(r, s, a).to_opinion()


def from_probability(p: float, n: float, a: float = 0.5) -> Opinion:
    """Create opinion from calibrated probability p with effective sample size n.

    r = p * n, s = (1-p) * n.
    """
    return from_evidence(p * n, (1.0 - p) * n, a)


def consensus_pair(a_op: Opinion, b_op: Opinion) -> Opinion:
    """Consensus of two opinions (Jøsang Theorem 7, p.25)."""
    kappa = a_op.u + b_op.u - a_op.u * b_op.u
    if abs(kappa) < _TOL:
        raise ValueError("Cannot fuse two dogmatic opinions (κ ≈ 0)")

    b = (a_op.b * b_op.u + b_op.b * a_op.u) / kappa
    d = (a_op.d * b_op.u + b_op.d * a_op.u) / kappa
    u = (a_op.u * b_op.u) / kappa

    # Base rate fusion
    denom_a = a_op.u + b_op.u - 2.0 * a_op.u * b_op.u
    if abs(denom_a) < _TOL:
        # Equal uncertainty — average the base rates
        a = (a_op.a + b_op.a) / 2.0
    else:
        a = (b_op.a * a_op.u + a_op.a * b_op.u - (a_op.a + b_op.a) * a_op.u * b_op.u) / denom_a

    return Opinion(b, d, u, a)


def consensus(*opinions: Opinion) -> Opinion:
    """Fold multiple opinions via pairwise consensus (associative)."""
    if len(opinions) == 0:
        raise ValueError("Need at least one opinion")
    result = opinions[0]
    for op in opinions[1:]:
        result = consensus_pair(result, op)
    return result


def discount(trust: Opinion, source: Opinion) -> Opinion:
    """Trust discounting (Jøsang Def 14, p.24)."""
    b = trust.b * source.b
    d = trust.b * source.d
    u = trust.d + trust.u + trust.b * source.u
    a = source.a
    return Opinion(b, d, u, a)
