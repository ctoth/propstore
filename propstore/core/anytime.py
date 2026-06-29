"""Anytime result sentinels for propstore's own bounded enumerators.

Zilberstein 1996 frames anytime algorithms as returning a partial result when a
resource bound interrupts exhaustive computation. propstore's bounded operations
(graph walks, witness searches, replay) raise these when they hit a
caller-supplied ceiling, leaving the unvisited remainder marked vacuous rather
than inferred — honest ignorance over fabricated confidence (CLAUDE.md).

These are propstore's *own* sentinels. The argumentation and belief-set packages
export their own ``EnumerationExceeded`` for their enumerations; propstore does
not mirror those — it uses each package's spelling where that package
enumerates, and this one only where propstore itself enumerates.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.provenance import ProvenanceStatus


@dataclass(frozen=True, slots=True)
class EnumerationExceeded(RuntimeError):
    """Exact enumeration stopped at a caller-supplied candidate ceiling.

    The unvisited remainder carries :attr:`remainder_provenance` (vacuous by
    default) so a partial result never masquerades as a complete one.
    """

    partial_count: int
    max_candidates: int
    remainder_provenance: ProvenanceStatus = ProvenanceStatus.VACUOUS

    def __str__(self) -> str:
        return (
            "exact enumeration exceeded "
            f"{self.max_candidates} candidates after "
            f"{self.partial_count} partial results"
        )


@dataclass(frozen=True, slots=True)
class BudgetExhausted(RuntimeError):
    """A bounded computation consumed its step/iteration budget before settling.

    Distinct from :class:`EnumerationExceeded`: that names too many *candidates*;
    this names too many *steps* (iterations of a fixpoint or replay) for the
    allotted budget. The result so far is partial, not a settled answer.
    """

    steps_taken: int
    max_steps: int
    remainder_provenance: ProvenanceStatus = ProvenanceStatus.VACUOUS

    def __str__(self) -> str:
        return (
            "bounded computation exhausted its budget of "
            f"{self.max_steps} steps after {self.steps_taken} steps"
        )
