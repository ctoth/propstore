"""Heavy journal-step projection with re-derived stances and conflicts.

Phase 3 properties P-HEAVY-1/2/3 cover this heavier projection mode.

The minimal projection (``at_journal_step(..., heavy=False)``) projects only
the claim-id set accepted at step k. The heavy variant additionally
re-derives stances and conflicts visible within that accepted claim set
from the belief-space query surface. ``state.scope.commit`` anchors the
cache key and proves the caller supplied a concrete worldline coordinate;
this module does not perform a Git checkout.

For ``WorldQuery`` inputs, replay rebuilds a temporary query surface from the
journal step's commit and returns the rows visible within that step.

Cache: results are keyed by ``(commit_sha, frozenset[claim_id])``. The
cache exposes hit/miss/size statistics via ``cache_stats()``.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from propstore.families.claims.declaration import Claim
from propstore.families.relations.declaration import ConflictWitness, Stance
from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.support_revision.state import RevisionScope
from propstore.world.types import ClaimView


@dataclass(frozen=True)
class HeavyCacheStats:
    hits: int
    misses: int
    size: int


class _ClaimLookupSpace(Protocol):
    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]: ...


@runtime_checkable
class _StanceConflictSpace(Protocol):
    def all_claim_stances(self) -> list[Stance]: ...
    def conflicts(self, concept_id: str | None = None) -> list[ConflictWitness]: ...


@runtime_checkable
class _HistoricalQuerySpace(Protocol):
    def historical_query(
        self,
        commit_sha: str,
    ) -> AbstractContextManager[_ClaimLookupSpace]: ...


_CACHE: dict[tuple[str, frozenset[str]], ClaimView] = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0


def reset_cache() -> None:
    """Reset cache + stats. For tests."""
    global _CACHE_HITS, _CACHE_MISSES
    _CACHE.clear()
    _CACHE_HITS = 0
    _CACHE_MISSES = 0


def cache_stats() -> HeavyCacheStats:
    return HeavyCacheStats(hits=_CACHE_HITS, misses=_CACHE_MISSES, size=len(_CACHE))


def replay_at_step(
    belief_space: _ClaimLookupSpace,
    journal: TransitionJournal,
    k: int,
) -> ClaimView:
    """Re-derive a ClaimView at journal step ``k`` against the snapshot's commit.

    Opens a repository-backed historical query surface when one is available,
    or falls back to the supplied belief-space query surface. Caches by
    ``(commit_sha, frozenset[claim_id])``.

    Honest scope contract: the ``@scope_policy(require={"heavy": ("commit",)})``
    decorator on ``at_journal_step`` guarantees ``state.scope.commit`` is
    set before this function is invoked. We re-assert it here as a
    defence-in-depth check.
    """
    global _CACHE_HITS, _CACHE_MISSES
    snap = journal.entries[k].state_out
    scope = snap.state.scope
    if not scope.commit:
        raise ValueError("journal_replay.replay_at_step requires snapshot.scope.commit")
    minimal_claim_ids = frozenset(snapshot_to_claim_ids(snap))
    cache_key = (str(scope.commit), minimal_claim_ids)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        _CACHE_HITS += 1
        return cached
    _CACHE_MISSES += 1

    if isinstance(belief_space, _HistoricalQuerySpace):
        with belief_space.historical_query(str(scope.commit)) as historical_space:
            view = _claim_view_from_space(
                historical_space,
                scope=scope,
                claim_ids=minimal_claim_ids,
            )
    else:
        view = _claim_view_from_space(
            belief_space,
            scope=scope,
            claim_ids=minimal_claim_ids,
        )
    _CACHE[cache_key] = view
    return view


def _claim_view_from_space(
    belief_space: _ClaimLookupSpace,
    *,
    scope: RevisionScope,
    claim_ids: frozenset[str],
) -> ClaimView:
    rows = belief_space.claims_by_ids(set(claim_ids))
    stances = _stances_within_step(belief_space, claim_ids)
    conflicts = _conflicts_within_step(belief_space, claim_ids)
    return ClaimView(
        claims=rows,
        scope=scope,
        bound=None,
        stances=stances,
        conflicts=conflicts,
    )


def _stances_within_step(
    belief_space: _ClaimLookupSpace,
    claim_ids: frozenset[str],
) -> tuple[Stance, ...]:
    if not isinstance(belief_space, _StanceConflictSpace):
        return ()
    return tuple(
        stance
        for stance in belief_space.all_claim_stances()
        if str(stance.claim_id) in claim_ids
        and str(stance.target_claim_id) in claim_ids
    )


def _conflicts_within_step(
    belief_space: _ClaimLookupSpace,
    claim_ids: frozenset[str],
) -> tuple[ConflictWitness, ...]:
    if not isinstance(belief_space, _StanceConflictSpace):
        return ()
    return tuple(
        conflict
        for conflict in belief_space.conflicts()
        if str(conflict.claim_a_id) in claim_ids
        and str(conflict.claim_b_id) in claim_ids
    )
