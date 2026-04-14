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

# Clamp range for fused base rates (review-2026-04-14 Issue 4).
#
# Van der Heijden 2018, Definition 4, requires all sources share a
# single base rate when fusing (the fused opinion inherits it
# unchanged). propstore routinely fuses opinions produced by different
# models/pipelines with distinct priors, so we instead compute a
# confidence-weighted blend across sources and clamp the result to
# this closed interval. Clamping avoids degenerate 0/1 priors which
# would make ``maximize_uncertainty`` divide by zero and collapse the
# ordering key (p.30 Def 16). The deviation is documented in
# ``papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic``
# and covered by ``TestWBFAdditionalProperties.test_base_rate_clamping``.
_BASE_RATE_CLAMP = (0.01, 0.99)


def _clamp_base_rate(a: float) -> float:
    """Clamp a fused base rate to ``_BASE_RATE_CLAMP``."""
    lo, hi = _BASE_RATE_CLAMP
    return max(lo, min(hi, a))


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

    def conjunction(self, other: Opinion) -> Opinion:
        """Subjective-logic conjunction (Jøsang 2001 Theorem 3, p.14).

        Binomial (binary frame) conjunction of two opinions on
        independent propositions. The base-rate formula ``a1 * a2``
        assumes binary frames; generalizations to k-nomial frames
        require the hyper-opinion machinery from van der Heijden 2018
        and are not implemented here.

        Prefer this explicit method over ``&`` in callers that might
        otherwise be confused with Python's ``and`` keyword — ``op1
        and op2`` short-circuits on truthiness and does NOT call
        ``__and__`` (see ``__bool__``).
        """
        b = self.b * other.b
        d = self.d + other.d - self.d * other.d
        u = self.b * other.u + self.u * other.b + self.u * other.u
        a = self.a * other.a
        return Opinion(b, d, u, a)

    def disjunction(self, other: Opinion) -> Opinion:
        """Subjective-logic disjunction (Jøsang 2001 Theorem 4, p.14-15).

        Binomial (binary frame) disjunction of two opinions on
        independent propositions. The base-rate formula
        ``a1 + a2 - a1*a2`` is the probabilistic OR of independent
        events and is correct only for binary frames; non-binary
        frames require the generalized fusion in van der Heijden 2018
        and are not implemented here.

        Prefer this explicit method over ``|`` in callers that might
        otherwise be confused with Python's ``or`` keyword.
        """
        b = self.b + other.b - self.b * other.b
        d = self.d * other.d
        u = self.d * other.u + self.u * other.d + self.u * other.u
        a = self.a + other.a - self.a * other.a
        return Opinion(b, d, u, a)

    def __and__(self, other: Opinion) -> Opinion:
        """Alias for :meth:`conjunction`."""
        return self.conjunction(other)

    def __or__(self, other: Opinion) -> Opinion:
        """Alias for :meth:`disjunction`."""
        return self.disjunction(other)

    def __bool__(self) -> bool:
        """Opinions are not truthy — always raises ``TypeError``.

        Python's ``and``/``or`` keywords short-circuit on truthiness
        and never dispatch to ``__and__``/``__or__`` (review-2026-04-14).
        Without this guard, ``if op1 and op2`` silently produces a
        truthy Opinion rather than the subjective-logic conjunction,
        and ``if opinion`` is indistinguishable from ``if opinion is
        not None``. Force callers to be explicit.
        """
        raise TypeError(
            "Opinion is not truthy; use `op is None` / `op is not None` for "
            "presence checks, `op.conjunction(other)` / `op & other` for "
            "subjective-logic conjunction, or compare `op.expectation()` "
            "for probability-like checks."
        )

    def _quantized(self) -> tuple[int, int, int, int]:
        """Project (b, d, u, a) onto the shared ``_TOL`` grid.

        Both ``__eq__`` and ``__hash__`` must use this single quantization
        so the hash contract holds (review-2026-04-14): the older
        tolerance-based ``__eq__`` paired with ``round(·, 8)`` hashing
        could silently disagree on opinions straddling a rounding
        boundary, corrupting dicts and sets.
        """
        return (
            round(self.b / _TOL),
            round(self.d / _TOL),
            round(self.u / _TOL),
            round(self.a / _TOL),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Opinion):
            return NotImplemented
        return self._quantized() == other._quantized()

    def __hash__(self) -> int:
        return hash(self._quantized())

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

        Precondition: ``0 < a < 1`` (enforced in ``__post_init__``)
        — the divisions by ``a`` and ``1 - a`` below depend on this
        strict bound. Relaxing the constructor's check would require
        an explicit guard here (review-2026-04-14 Issue 7).
        """
        e = self.expectation()
        a = self.a

        # Upper bounds on u from b >= 0 and d >= 0.
        # Safe because __post_init__ enforces 0 < a < 1 strictly.
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
    """Consensus of two opinions (Jøsang Theorem 7, p.25).

    Base-rate fusion uses the cancellation-free form
    ``a_b·u_a·v_b + a_a·u_b·v_a  /  u_a·v_b + u_b·v_a``
    where ``v = 1 - u`` (review-2026-04-14 Issue 3). The obvious form
    ``u_a + u_b - 2·u_a·u_b`` suffers catastrophic cancellation when
    both ``u`` values approach 1, causing the fused base rate to
    drift tens of ULPs away from the analytically exact answer.
    """
    kappa = a_op.u + b_op.u - a_op.u * b_op.u
    if abs(kappa) < _TOL:
        raise ValueError("Cannot fuse two dogmatic opinions (κ ≈ 0)")

    b = (a_op.b * b_op.u + b_op.b * a_op.u) / kappa
    d = (a_op.d * b_op.u + b_op.d * a_op.u) / kappa
    u = (a_op.u * b_op.u) / kappa

    # Base rate fusion — confidence-weighted average, written in the
    # cancellation-free v = 1 - u form so near-vacuous pairs stay stable.
    v_a = 1.0 - a_op.u
    v_b = 1.0 - b_op.u
    denom_a = a_op.u * v_b + b_op.u * v_a
    if denom_a < _TOL:
        # Both sources are (near-)vacuous → zero confidence in either
        # base rate. Fall back to a plain average; this is the
        # degenerate limit of the confidence-weighted form.
        a = (a_op.a + b_op.a) / 2.0
    else:
        a = (b_op.a * a_op.u * v_b + a_op.a * b_op.u * v_a) / denom_a

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
    """Trust discounting (Jøsang Def 14, p.24).

    Jøsang's explicit form::

        b = trust.b * source.b
        d = trust.b * source.d
        u = 1 - b - d
          = 1 - trust.b * (source.b + source.d)
          = 1 - trust.b * (1 - source.u)
          = trust.d + trust.u + trust.b * source.u   (since
                                                       trust.b + trust.d
                                                       + trust.u = 1)

    We write the expanded form directly so the identity is visible and
    we don't have to reconstruct u from (1 - b - d) at runtime. The
    derivation only holds because trust is a well-formed Opinion
    (b + d + u = 1).
    """
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

    # Clamp to `_BASE_RATE_CLAMP` — see constant's comment for the
    # deviation from van der Heijden 2018.
    a_fused = _clamp_base_rate(a_fused)

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
    """Binomial reduction of CCF (van der Heijden 2018, Definition 5).

    Used internally by ``ccf()`` when at least one opinion is dogmatic.

    For a binomial frame, van der Heijden's three-phase algorithm
    (consensus extraction → compromise → normalization) collapses to
    plain arithmetic averaging of the four components:

      b_fused = mean(b_i)
      d_fused = mean(d_i)
      u_fused = mean(u_i)
      a_fused = mean(a_i)

    Algebraic proof that the explicit three phases reduce to averaging:
    consensus_b + mean(b_i − consensus_b) = mean(b_i); sym. for d. So
    the original consensus/compromise decomposition is a no-op on
    binary frames, and the (b_i + d_i + u_i = 1) invariant means the
    sum-to-one normalization is redundant as well.

    Review-2026-04-14 Issue 2: the old form's explicit normalization
    suggested that ``u`` could be rescaled alongside ``b``/``d``,
    conflating residual ignorance with belief mass. Writing it as
    direct averaging makes the preserved-uncertainty contract obvious.
    """
    N = len(opinions)
    if N == 1:
        return opinions[0]

    b_fused = sum(op.b for op in opinions) / N
    d_fused = sum(op.d for op in opinions) / N
    u_fused = sum(op.u for op in opinions) / N

    # Clamp tiny negative drift to zero before handing to the constructor.
    b_fused = max(0.0, b_fused)
    d_fused = max(0.0, d_fused)
    u_fused = max(0.0, u_fused)

    # Base-rate fusion: see `_BASE_RATE_CLAMP` for the deviation from
    # van der Heijden 2018 (which requires shared priors).
    a_fused = _clamp_base_rate(sum(op.a for op in opinions) / N)

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
