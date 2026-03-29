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

    # --- Ordering (Jøsang 2001 Def 10, p.9) ---

    def _ordering_key(self) -> tuple[float, float, float]:
        """Return (E(x), -u, -a) for total ordering.

        Jøsang 2001 Def 10: compare by E(x) ascending, then by u
        descending (less uncertainty is greater), then by a descending
        (less base rate is greater).
        """
        return (self.expectation(), -self.u, -self.a)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return self._ordering_key() < other._ordering_key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return self._ordering_key() <= other._ordering_key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return self._ordering_key() > other._ordering_key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return self._ordering_key() >= other._ordering_key()

    # --- Uncertainty Maximization (Jøsang 2001 Def 16, p.30) ---

    def maximize_uncertainty(self) -> Opinion:
        """Maximize u while preserving E(x) = b + a*u.

        Jøsang 2001 p.30: for non-repeatable events, redistribute
        belief mass to maximize uncertainty. Constraints:
          b + d + u = 1, b >= 0, d >= 0, u >= 0
          b + a*u = E (constant)

        u_max = min(E/a, (1-E)/(1-a))
        """
        e = self.expectation()
        a = self.a

        # Upper bounds on u from b >= 0 and d >= 0
        u_from_b = e / a            # b = E - a*u >= 0
        u_from_d = (1.0 - e) / (1.0 - a)  # d = 1 - E - u*(1-a) >= 0

        u_max = min(u_from_b, u_from_d)
        # Clamp to [0, 1] for numerical safety
        u_max = max(0.0, min(1.0, u_max))

        b_new = e - a * u_max
        d_new = 1.0 - u_max - b_new

        # Clamp negatives from float drift
        b_new = max(0.0, b_new)
        d_new = max(0.0, d_new)

        return Opinion(b_new, d_new, u_max, a)


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


def wbf(*opinions: Opinion) -> Opinion:
    """N-source Weighted Belief Fusion (van der Heijden 2018, Definition 4).

    Generalizes consensus_pair to N sources. Each source is weighted by
    its certainty (1/u_i). For N=2, produces identical results to
    consensus_pair().

    Raises ValueError for empty input or if any opinion is dogmatic
    (u < _TOL), since WBF's denominator diverges.
    """
    if len(opinions) == 0:
        raise ValueError("Need at least one opinion")
    if len(opinions) == 1:
        return opinions[0]

    N = len(opinions)
    for i, op in enumerate(opinions):
        if op.u < _TOL:
            raise ValueError(
                f"Opinion {i} is dogmatic (u={op.u}). "
                "Use fuse(method='auto') or ccf() for dogmatic sources."
            )

    # Precompute products of all uncertainties excluding each index.
    # prod_except[i] = product(u_j for j != i)
    total_prod = math.prod(op.u for op in opinions)
    prod_except = [total_prod / op.u for op in opinions]

    # Numerators: b_fused_num = sum(b_i * prod(u_j, j!=i))
    num_b = sum(
        op.b * prod_except[i]
        for i, op in enumerate(opinions)
    )
    num_d = sum(
        op.d * prod_except[i]
        for i, op in enumerate(opinions)
    )
    num_u = total_prod

    # Normalizing denominator kappa = sum(prod(u_j, j!=i)) - (N-1)*prod(u_j)
    kappa = sum(prod_except) - (N - 1) * total_prod

    if abs(kappa) < _TOL:
        raise ValueError("WBF denominator κ ≈ 0")

    b_fused = num_b / kappa
    d_fused = num_d / kappa
    u_fused = num_u / kappa

    # Clamp for float drift
    b_fused = max(0.0, b_fused)
    d_fused = max(0.0, d_fused)
    u_fused = max(0.0, u_fused)

    # Base rate fusion (Jøsang Theorem 7 generalized):
    # weight_i = (1 - u_i) * prod(u_j for j != i)
    weights = [(1.0 - op.u) * prod_except[i] for i, op in enumerate(opinions)]
    total_weight = sum(weights)
    if total_weight < _TOL:
        # All vacuous — average base rates
        a_fused = sum(op.a for op in opinions) / N
    else:
        a_fused = sum(
            op.a * w for op, w in zip(opinions, weights)
        ) / total_weight

    # Clamp base rate to valid range
    a_fused = max(0.01, min(0.99, a_fused))

    return Opinion(b_fused, d_fused, u_fused, a_fused)


def ccf(*opinions: Opinion) -> Opinion:
    """Cumulative & Compromise Fusion (van der Heijden 2018, Definition 5).

    Handles the case where WBF cannot — dogmatic sources (u ≈ 0).

    Algorithm:
    - If no dogmatic opinions: delegates to wbf() (which is associative).
    - If all dogmatic: averages belief masses (min+average three-phase).
    - If mixed: fuses non-dogmatic via wbf(), then averages with dogmatic
      opinions using the three-phase min+average method.
    """
    if len(opinions) == 0:
        raise ValueError("Need at least one opinion")
    if len(opinions) == 1:
        return opinions[0]

    dogmatic = [op for op in opinions if op.u < _TOL]
    non_dogmatic = [op for op in opinions if op.u >= _TOL]

    # Case 1: All non-dogmatic — delegate to WBF (correct & associative).
    if not dogmatic:
        return wbf(*non_dogmatic)

    # Case 2: All dogmatic — three-phase min+average on belief masses.
    if not non_dogmatic:
        return _ccf_average(dogmatic)

    # Case 3: Mixed — fuse non-dogmatic via WBF, then min+average with dogmatic.
    wbf_result = wbf(*non_dogmatic)
    return _ccf_average([*dogmatic, wbf_result])


def _ccf_average(opinions: list[Opinion]) -> Opinion:
    """Three-phase min+average CCF for dogmatic (or near-dogmatic) opinions.

    Used internally by ccf() when at least one opinion is dogmatic.
    Phase 1: consensus extraction (min belief/disbelief).
    Phase 2: compromise on residuals (average beyond consensus).
    Phase 3: combine and normalize.
    """
    N = len(opinions)
    if N == 1:
        return opinions[0]

    # Phase 1 — Consensus extraction: minimum belief/disbelief across sources.
    consensus_b = min(op.b for op in opinions)
    consensus_d = min(op.d for op in opinions)

    # Phase 2 — Compromise on residuals: average of what each source
    # contributes beyond the consensus.
    compromise_b = sum(op.b - consensus_b for op in opinions) / N
    compromise_d = sum(op.d - consensus_d for op in opinions) / N

    # Phase 3 — Combine and normalize.
    raw_b = consensus_b + compromise_b
    raw_d = consensus_d + compromise_d
    # Uncertainty: average of source uncertainties (0 for dogmatic).
    raw_u = sum(op.u for op in opinions) / N

    raw_sum = raw_b + raw_d + raw_u
    if raw_sum < _TOL:
        # Degenerate case — return vacuous
        a_fused = sum(op.a for op in opinions) / N
        a_fused = max(0.01, min(0.99, a_fused))
        return Opinion(0.0, 0.0, 1.0, a_fused)

    # Normalize so b + d + u = 1
    b_fused = max(0.0, raw_b / raw_sum)
    d_fused = max(0.0, raw_d / raw_sum)
    u_fused = max(0.0, raw_u / raw_sum)

    a_fused = sum(op.a for op in opinions) / N
    a_fused = max(0.01, min(0.99, a_fused))

    return Opinion(b_fused, d_fused, u_fused, a_fused)


def fuse(*opinions: Opinion, method: str = "auto") -> Opinion:
    """Dispatch to WBF or CCF.

    Parameters
    ----------
    method : str
        "wbf" — always WBF (raises on dogmatic inputs)
        "ccf" — always CCF
        "auto" — try WBF first; fall back to CCF on dogmatic inputs
    """
    if method == "wbf":
        return wbf(*opinions)
    elif method == "ccf":
        return ccf(*opinions)
    elif method == "auto":
        try:
            return wbf(*opinions)
        except ValueError:
            return ccf(*opinions)
    else:
        raise ValueError(f"Unknown fusion method: {method!r}")
