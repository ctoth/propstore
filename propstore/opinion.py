"""Provenance-threading adapter over the ``doxa`` Subjective Logic kernel.

The subjective-logic algebra (Jøsang 2001; van der Heijden et al. 2018) lives
in the standalone, dependency-free ``doxa`` package. This module is a thin
*adapter*: it subclasses ``doxa.Opinion`` to add a ``provenance`` field and
overrides every Opinion-producing operation so the result carries — or
composes — provenance. It contains NO subjective-logic arithmetic of its own;
every operation defers to ``super()`` for the math.

The provenance model (``Provenance``, ``ProvenanceStatus``,
``compose_provenance``) is propstore-specific and stays in
``propstore.provenance``. The kernel never touches it.

Design (notes/doxa-extraction.md, decisions 1-6):

* ``doxa`` is the pure kernel; provenance does not extract.
* propstore adapts by subclassing — ``class Opinion(doxa.Opinion)``.
* unary/passthrough ops (``__invert__``, ``maximize_uncertainty``) carry
  ``self.provenance`` unchanged.
* composing ops (``conjunction``, ``disjunction``, ``&``, ``|``,
  ``consensus_pair``, ``discount``, ``consensus``, ``wbf``, ``ccf``, ``fuse``)
  compose every operand's provenance via ``compose_provenance``; ``None``
  operands drop out, all-``None`` yields ``None``.
* the free functions of the pre-extraction module are GONE — they are kernel
  methods now and callers invoke ``Opinion.<method>`` directly. No shims.
"""

from __future__ import annotations

from doxa import BetaEvidence as _DoxaBetaEvidence
from doxa import Opinion as _DoxaOpinion
from doxa.opinion import W

from propstore.provenance import Provenance, ProvenanceStatus, compose_provenance

__all__ = ["W", "BetaEvidence", "Opinion"]


def _compose_opinion_provenance(
    operation: str,
    *opinions: _DoxaOpinion,
) -> Provenance | None:
    """Compose provenance across ``opinions`` for a derived value.

    ``None``-provenance operands drop out of the composition (mirrors the
    pre-extraction ``_compose_opinion_provenance``); when no operand carries
    provenance the derived value carries ``None``.
    """
    records = tuple(
        opinion.provenance
        for opinion in opinions
        if isinstance(opinion, Opinion) and opinion.provenance is not None
    )
    if not records:
        return None
    return compose_provenance(*records, operation=operation)


class Opinion(_DoxaOpinion):
    """A ``doxa`` subjective opinion ω = (b, d, u, a) carrying provenance.

    Subclasses the pure kernel ``doxa.Opinion``; the only additional state is
    the optional ``provenance`` field. Every operation that produces an
    ``Opinion`` is overridden to thread provenance — the algebra itself is
    inherited unchanged from the kernel.

    The field order ``b, d, u, a, provenance, allow_dogmatic`` matches the
    pre-extraction module so positional callers that pass provenance as the
    fifth argument keep working.
    """

    provenance: Provenance | None = None

    def __init__(
        self,
        b: float,
        d: float,
        u: float,
        a: float,
        provenance: Provenance | None = None,
        allow_dogmatic: bool = False,
    ) -> None:
        # doxa.Opinion is a frozen dataclass; its __init__ takes
        # (b, d, u, a, allow_dogmatic). Run the kernel constructor for the
        # mass-sum / range / dogmatic validation, then attach provenance
        # through the frozen-dataclass escape hatch.
        super().__init__(b, d, u, a, allow_dogmatic=allow_dogmatic)
        object.__setattr__(self, "provenance", provenance)

    def __repr__(self) -> str:
        return (
            f"Opinion(b={self.b!r}, d={self.d!r}, u={self.u!r}, a={self.a!r}, "
            f"provenance={self.provenance!r}, allow_dogmatic={self.allow_dogmatic!r})"
        )

    # --- Provenance accessors -------------------------------------------

    @property
    def provenance_status(self) -> ProvenanceStatus:
        """Return the explicit provenance status for this probability value."""
        if self.provenance is None:
            raise ValueError(
                "Opinion requires explicit provenance to expose provenance status"
            )
        return self.provenance.status

    def with_provenance(self, provenance: Provenance) -> Opinion:
        """Return the same opinion with explicit provenance attached."""
        return Opinion(
            self.b,
            self.d,
            self.u,
            self.a,
            provenance,
            allow_dogmatic=self.allow_dogmatic,
        )

    # --- Re-wrap kernel results into provenance-bearing opinions --------

    @staticmethod
    def _bare(opinion: _DoxaOpinion) -> _DoxaOpinion:
        """Project any opinion onto a bare ``doxa.Opinion`` (no provenance).

        Feeding kernel algorithms bare instances keeps the math purely in
        ``doxa`` and avoids re-entering this adapter's provenance-composing
        overrides part-way through a multi-source fold.
        """
        if type(opinion) is _DoxaOpinion:
            return opinion
        return _DoxaOpinion(
            opinion.b,
            opinion.d,
            opinion.u,
            opinion.a,
            allow_dogmatic=opinion.allow_dogmatic,
        )

    @classmethod
    def _carry(cls, kernel: _DoxaOpinion, provenance: Provenance | None) -> Opinion:
        """Rebuild a kernel-computed opinion as a propstore ``Opinion``.

        The kernel's operations build bare ``doxa.Opinion`` instances; this
        copies the computed ``(b, d, u, a, allow_dogmatic)`` and attaches
        ``provenance``. No subjective-logic math happens here.
        """
        return cls(
            kernel.b,
            kernel.d,
            kernel.u,
            kernel.a,
            provenance,
            allow_dogmatic=kernel.allow_dogmatic,
        )

    # --- Special constructors ------------------------------------------

    @classmethod
    def vacuous(cls, a: float, *, provenance: Provenance | None = None) -> Opinion:
        """Total ignorance."""
        return cls._carry(_DoxaOpinion.vacuous(a), provenance)

    @classmethod
    def dogmatic_true(
        cls, a: float, *, provenance: Provenance | None = None
    ) -> Opinion:
        """Absolute belief."""
        return cls._carry(_DoxaOpinion.dogmatic_true(a), provenance)

    @classmethod
    def dogmatic_false(
        cls, a: float, *, provenance: Provenance | None = None
    ) -> Opinion:
        """Absolute disbelief."""
        return cls._carry(_DoxaOpinion.dogmatic_false(a), provenance)

    @classmethod
    def from_evidence(
        cls,
        r: float,
        s: float,
        a: float,
        *,
        provenance: Provenance | None = None,
    ) -> Opinion:
        """Create opinion from evidence counts."""
        return cls._carry(_DoxaOpinion.from_evidence(r, s, a), provenance)

    @classmethod
    def from_probability(
        cls,
        p: float,
        n: float,
        a: float,
        *,
        provenance: Provenance | None = None,
    ) -> Opinion:
        """Create opinion from calibrated probability ``p`` with sample size ``n``."""
        return cls._carry(_DoxaOpinion.from_probability(p, n, a), provenance)

    # --- Conversion ----------------------------------------------------

    def to_beta_evidence(self) -> BetaEvidence:
        """Opinion -> :class:`BetaEvidence`.

        ``BetaEvidence`` has no provenance field, so an Opinion->Beta->Opinion
        roundtrip loses provenance — preserved deliberately
        (notes/doxa-extraction.md "Risks"). The kernel does the (r, s, a) math;
        this only re-types the result as the propstore ``BetaEvidence`` wrapper.
        """
        kernel = super().to_beta_evidence()
        return BetaEvidence(kernel.r, kernel.s, kernel.a)

    # --- Unary / passthrough operators (carry self.provenance) ----------

    def __invert__(self) -> Opinion:
        """Negation ``~ω`` — carries ``self.provenance`` unchanged."""
        return self._carry(super().__invert__(), self.provenance)

    def maximize_uncertainty(self) -> Opinion:
        """Uncertainty maximization — carries ``self.provenance`` unchanged."""
        return self._carry(super().maximize_uncertainty(), self.provenance)

    # --- Composing binary operators (compose both operands) -------------

    def conjunction(self, other: _DoxaOpinion) -> Opinion:
        """Subjective-logic conjunction — composes both operands' provenance."""
        return self._carry(
            super().conjunction(other),
            _compose_opinion_provenance("conjunction", self, other),
        )

    def disjunction(self, other: _DoxaOpinion) -> Opinion:
        """Subjective-logic disjunction — composes both operands' provenance."""
        return self._carry(
            super().disjunction(other),
            _compose_opinion_provenance("disjunction", self, other),
        )

    def __and__(self, other: _DoxaOpinion) -> Opinion:
        """Alias for :meth:`conjunction`."""
        return self.conjunction(other)

    def __or__(self, other: _DoxaOpinion) -> Opinion:
        """Alias for :meth:`disjunction`."""
        return self.disjunction(other)

    def consensus_pair(self, other: _DoxaOpinion) -> Opinion:
        """Pairwise consensus — composes both operands' provenance via fusion."""
        return self._carry(
            super().consensus_pair(other),
            _compose_opinion_provenance("fusion", self, other),
        )

    def discount(self, source: _DoxaOpinion) -> Opinion:
        """Trust discounting — composes trust and source provenance."""
        return self._carry(
            super().discount(source),
            _compose_opinion_provenance("discount", self, source),
        )

    # --- N-source composing operators ----------------------------------

    @classmethod
    def _single_source(cls, opinion: _DoxaOpinion) -> Opinion:
        """Return a one-element fold's sole operand with its provenance intact.

        Mirrors the kernel's ``len == 1`` shortcut: a single-source fusion is
        the source itself, so its provenance is carried unchanged (handoff
        point 7, reports/doxa-g3-tester.md).
        """
        if isinstance(opinion, Opinion):
            return opinion
        return cls._carry(opinion, None)

    @classmethod
    def consensus(cls, *opinions: _DoxaOpinion) -> Opinion:
        """Fold opinions via pairwise consensus — composes every provenance."""
        if not opinions:
            raise ValueError("Need at least one opinion")
        if len(opinions) == 1:
            return cls._single_source(opinions[0])
        return cls._carry(
            _DoxaOpinion.consensus(*(cls._bare(op) for op in opinions)),
            _compose_opinion_provenance("fusion", *opinions),
        )

    @classmethod
    def wbf(cls, *opinions: _DoxaOpinion) -> Opinion:
        """N-source Weighted Belief Fusion — composes every operand's provenance."""
        if not opinions:
            raise ValueError("Need at least one opinion")
        if len(opinions) == 1:
            return cls._single_source(opinions[0])
        return cls._carry(
            _DoxaOpinion.wbf(*(cls._bare(op) for op in opinions)),
            _compose_opinion_provenance("fusion", *opinions),
        )

    @classmethod
    def ccf(cls, *opinions: _DoxaOpinion) -> Opinion:
        """N-source Consensus & Compromise Fusion — composes every provenance."""
        if not opinions:
            raise ValueError("Need at least one opinion")
        if len(opinions) == 1:
            return cls._single_source(opinions[0])
        return cls._carry(
            _DoxaOpinion.ccf(*(cls._bare(op) for op in opinions)),
            _compose_opinion_provenance("fusion", *opinions),
        )

    @classmethod
    def fuse(cls, *opinions: _DoxaOpinion, method: str = "auto") -> Opinion:
        """Dispatch to WBF or CCF — composes every operand's provenance."""
        if not opinions:
            raise ValueError("Need at least one opinion")
        if len(opinions) == 1:
            return cls._single_source(opinions[0])
        return cls._carry(
            _DoxaOpinion.fuse(*(cls._bare(op) for op in opinions), method=method),
            _compose_opinion_provenance("fusion", *opinions),
        )


class BetaEvidence(_DoxaBetaEvidence):
    """Provenance-aware adapter over the pure ``doxa.BetaEvidence``.

    Subclasses the kernel ``doxa.BetaEvidence`` (fields ``r, s, a``); it adds
    no state of its own. ``doxa.BetaEvidence`` carries no provenance — an
    Opinion->Beta->Opinion roundtrip therefore loses provenance
    (notes/doxa-extraction.md "Risks"; preserved deliberately). This subclass
    exists only so ``to_opinion`` can accept a ``provenance=`` kwarg and
    return a propstore :class:`Opinion`.
    """

    def to_opinion(self, *, provenance: Provenance | None = None) -> Opinion:
        """BetaEvidence -> propstore Opinion, attaching ``provenance``.

        The kernel does the (r, s, a) -> (b, d, u) math; this only re-types
        the result as a propstore :class:`Opinion` carrying ``provenance``.
        """
        kernel = super().to_opinion()
        return Opinion(
            kernel.b,
            kernel.d,
            kernel.u,
            kernel.a,
            provenance,
            allow_dogmatic=kernel.allow_dogmatic,
        )
