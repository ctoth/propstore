"""Pair a subjective-logic opinion with its typed provenance.

The subjective-logic ``Opinion`` algebra is owned by the ``doxa`` package and is
deliberately provenance-free (a pure Jøsang/van-der-Heijden kernel). propstore's
delta over that kernel is the honest-ignorance discipline of CLAUDE.md: every
probability-bearing value that enters the argumentation layer must say *where it
came from* — ``measured`` / ``calibrated`` / ``stated`` / ``defaulted`` /
``vacuous`` — rather than fabricate a number.

We carry that as a *pairing beside* the opinion, not by re-spelling the opinion
type. :class:`OpinionWithProvenance` HOLDS-A :class:`doxa.Opinion` by composition
and adds a :class:`~propstore.provenance.Provenance`. There is exactly one
canonical ``Opinion`` spelling — doxa's (CLAUDE.md substrate-boundary rule); this
module never defines a second one.

Honest ignorance: a *missing* opinion is not a fabricated finite number. It
becomes :meth:`doxa.Opinion.vacuous` carrying :data:`ProvenanceStatus.VACUOUS`
(Jøsang 2001, p.8 — the vacuous opinion represents total ignorance).
"""

from __future__ import annotations

from dataclasses import dataclass

from doxa import Opinion

from propstore.provenance import Provenance, ProvenanceStatus


@dataclass(frozen=True)
class OpinionWithProvenance:
    """A ``doxa.Opinion`` paired with the typed provenance of its value.

    This is composition, not subtyping: :attr:`opinion` *is* a ``doxa.Opinion``
    used directly, and :attr:`provenance` records how that opinion's value came to
    be. The read-through accessors (:attr:`uncertainty`, :attr:`base_rate`,
    :meth:`expectation`) forward to the held opinion so callers do not reach
    through two layers for the common honesty-layer queries; they are convenience
    forwarders, never a re-implementation of the algebra.
    """

    opinion: Opinion
    provenance: Provenance

    @property
    def uncertainty(self) -> float:
        """Forward to the held opinion's uncertainty mass ``u``."""

        return self.opinion.uncertainty

    @property
    def base_rate(self) -> float:
        """Forward to the held opinion's base rate ``a``."""

        return self.opinion.base_rate

    @property
    def is_vacuous(self) -> bool:
        """True when the opinion carries (near-)total ignorance (``u`` ≈ 1)."""

        return self.opinion.uncertainty > 0.99

    def expectation(self) -> float:
        """Forward to the held opinion's projected probability ``E(ω)``."""

        return self.opinion.expectation()


def _vacuous_provenance() -> Provenance:
    """Provenance for a value that is absent rather than measured."""

    return Provenance(status=ProvenanceStatus.VACUOUS)


def opinion_or_vacuous(
    opinion: Opinion | None,
    *,
    base_rate: float,
    provenance: Provenance | None = None,
) -> OpinionWithProvenance:
    """Pair an opinion with provenance, mapping a missing opinion to ignorance.

    When ``opinion`` is ``None`` the value is genuinely unknown: it becomes
    ``doxa.Opinion.vacuous(base_rate)`` carrying ``VACUOUS`` provenance, never a
    made-up finite belief (CLAUDE.md "honest ignorance over fabricated
    confidence"). When an opinion is supplied without explicit provenance, the
    pairing records ``VACUOUS`` status for the *provenance* — the opinion's value
    is present but its origin was not asserted.
    """

    if opinion is None:
        return OpinionWithProvenance(
            opinion=Opinion.vacuous(base_rate),
            provenance=provenance if provenance is not None else _vacuous_provenance(),
        )
    return OpinionWithProvenance(
        opinion=opinion,
        provenance=provenance if provenance is not None else _vacuous_provenance(),
    )
