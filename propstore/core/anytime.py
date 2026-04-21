"""Anytime result sentinels for bounded exact enumerators."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.provenance import ProvenanceStatus


@dataclass(frozen=True, slots=True)
class EnumerationExceeded(RuntimeError):
    """Exact enumeration stopped at a caller-supplied candidate ceiling.

    Zilberstein 1996 frames anytime algorithms as returning a partial
    result when resource bounds interrupt exhaustive computation. Propstore
    uses this sentinel, returned or raised as the call shape requires, when
    an exact enumerator has more candidates than the caller allowed, with the
    unvisited remainder marked vacuous rather than inferred.
    """

    partial_count: int
    max_candidates: int
    remainder_provenance: ProvenanceStatus = ProvenanceStatus.VACUOUS

    def __str__(self) -> str:
        return (
            "exact enumeration exceeded "
            f"{self.max_candidates} candidates after {self.partial_count} partial results"
        )
