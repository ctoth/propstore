"""Heavy variant of ``at_journal_step`` — re-derived stances and conflicts.

Per quire/plans/worldline-journal-bridge-2026-05-02.md sections 7 + 11
(Phase 3 properties P-HEAVY-1/2/3).

The minimal bridge (``at_journal_step(..., heavy=False)``) projects only
the claim-id set accepted at step k. The heavy variant additionally
re-derives stances and conflicts visible within that accepted claim set
from the belief-space query surface. ``state.scope.commit`` anchors the
cache key and proves the caller supplied a concrete worldline coordinate;
this module does not perform a Git checkout.

For property testing we register fixture commits explicitly via
``register_fixture_commit(commit_sha, claim_ids, stances, conflicts)``.
For production ``WorldQuery`` inputs, replay rebuilds a temporary query
surface from the journal step's commit and returns the rows visible within
that step.

Cache: results are keyed by ``(commit_sha, frozenset[claim_id])``. The
cache exposes hit/miss/size statistics via ``cache_stats()``.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from propstore.core.row_types import ClaimRow, ConflictRow, StanceRow
from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.support_revision.state import RevisionScope
from propstore.world.types import ClaimView


@dataclass(frozen=True)
class HeavyCacheStats:
    hits: int
    misses: int
    size: int


@dataclass(frozen=True)
class _FixtureCommit:
    """A pre-registered commit for property testing.

    Production replay reads rows from the belief-space query surface. For
    property tests we register the result explicitly so cache behaviour
    and stance/conflict surfacing can be exercised at N=1000 without git
    overhead.
    """

    commit_sha: str
    claim_ids: frozenset[str]
    stances: tuple[StanceRow, ...]
    conflicts: tuple[ConflictRow, ...]


class _ClaimLookupSpace(Protocol):
    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, ClaimRow]: ...


@runtime_checkable
class _StanceConflictSpace(Protocol):
    def all_claim_stances(self) -> list[StanceRow]: ...
    def conflicts(self, concept_id: str | None = None) -> list[ConflictRow]: ...


@runtime_checkable
class _HistoricalQuerySpace(Protocol):
    def historical_query(
        self,
        commit_sha: str,
    ) -> AbstractContextManager[_ClaimLookupSpace]: ...


_FIXTURE_REGISTRY: dict[str, _FixtureCommit] = {}
_CACHE: dict[tuple[str, frozenset[str]], ClaimView] = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0


def register_fixture_commit(
    commit_sha: str,
    *,
    claim_ids: frozenset[str],
    stances: tuple[StanceRow, ...] = (),
    conflicts: tuple[ConflictRow, ...] = (),
) -> None:
    """Register a fixture commit for property/integration testing.

    Production replay for unregistered commits uses a repository-backed
    historical query surface when one is available. Property tests use the
    registry to exercise the heavy code path without git overhead.
    """
    _FIXTURE_REGISTRY[commit_sha] = _FixtureCommit(
        commit_sha=commit_sha,
        claim_ids=frozenset(claim_ids),
        stances=tuple(stances),
        conflicts=tuple(conflicts),
    )


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

    Walks the registered fixture commit, opens a repository-backed
    historical query surface, or falls back to the supplied belief-space
    query surface. Caches by ``(commit_sha, frozenset[claim_id])``.

    Honest scope contract: the ``@scope_policy(require={"heavy": ("commit",)})``
    decorator on ``at_journal_step`` guarantees ``state.scope.commit`` is
    set before this function is invoked. We re-assert it here as a
    defence-in-depth check.
    """
    global _CACHE_HITS, _CACHE_MISSES
    snap = journal.entries[k].state_out
    scope = snap.state.scope
    if not scope.commit:
        raise ValueError(
            "journal_replay.replay_at_step requires snapshot.scope.commit"
        )
    minimal_claim_ids = frozenset(snapshot_to_claim_ids(snap))
    cache_key = (str(scope.commit), minimal_claim_ids)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        _CACHE_HITS += 1
        return cached
    _CACHE_MISSES += 1

    fixture = _FIXTURE_REGISTRY.get(str(scope.commit))
    if fixture is None:
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
    else:
        full_ids = set(minimal_claim_ids) | set(fixture.claim_ids)
        rows = belief_space.claims_by_ids(full_ids)
        view = ClaimView(
            claims=rows,
            scope=scope,
            bound=None,
            stances=fixture.stances,
            conflicts=fixture.conflicts,
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
) -> tuple[StanceRow, ...]:
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
) -> tuple[ConflictRow, ...]:
    if not isinstance(belief_space, _StanceConflictSpace):
        return ()
    return tuple(
        conflict
        for conflict in belief_space.conflicts()
        if str(conflict.claim_a_id) in claim_ids
        and str(conflict.claim_b_id) in claim_ids
    )
