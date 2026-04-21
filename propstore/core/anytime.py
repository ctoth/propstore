"""Anytime result sentinels for bounded exact enumerators."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.provenance import ProvenanceStatus


@dataclass(frozen=True, slots=True)
class EnumerationExceeded:
    """Exact enumeration stopped at a caller-supplied candidate ceiling.

    Zilberstein 1996 frames anytime algorithms as returning a partial
    result when resource bounds interrupt exhaustive computation. Propstore
    uses this sentinel when an exact enumerator has more candidates than the
    caller allowed, with the unvisited remainder marked vacuous rather than
    inferred.
    """

    partial_count: int
    max_candidates: int
    remainder_provenance: ProvenanceStatus = ProvenanceStatus.VACUOUS
