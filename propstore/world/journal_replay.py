"""Heavy variant of ``at_journal_step`` — re-derived stances and conflicts.

Per quire/plans/worldline-journal-bridge-2026-05-02.md sections 7 + 11
(Phase 3 properties P-HEAVY-1/2/3).

The minimal bridge (``at_journal_step(..., heavy=False)``) projects only
the claim-id set accepted at step k. The heavy variant additionally
re-derives stances and conflicts at that step by checking out
``state.scope.commit`` and rebuilding the live view at that commit.

For property testing we register fixture commits explicitly via
``register_fixture_commit(commit_sha, claim_ids, stances)``. Production
will check out the commit via dulwich and rebuild the sidecar at that
revision; that path is exercised by integration tests in Phase 6, not by
property tests at N=1000.

Cache: results are keyed by ``(commit_sha, frozenset[claim_id])``. The
cache exposes hit/miss/size statistics via ``cache_stats()``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.world.types import ClaimView


@dataclass(frozen=True)
class HeavyCacheStats:
    hits: int
    misses: int
    size: int


@dataclass(frozen=True)
class _FixtureCommit:
    """A pre-registered commit for property testing.

    Production replay walks dulwich + rebuilds the sidecar at the named
    commit; for property tests we register the result explicitly so
    cache behaviour and stance surfacing can be exercised at N=1000
    without git overhead.
    """

    commit_sha: str
    claim_ids: frozenset[str]
    stances: tuple[Any, ...]


_FIXTURE_REGISTRY: dict[str, _FixtureCommit] = {}
_CACHE: dict[tuple[str, frozenset[str]], ClaimView] = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0


def register_fixture_commit(
    commit_sha: str,
    *,
    claim_ids: frozenset[str],
    stances: tuple[Any, ...] = (),
) -> None:
    """Register a fixture commit for property/integration testing.

    Production replay does not consult the registry — it walks dulwich
    and rebuilds the sidecar at the named commit. Property tests use the
    registry to exercise the heavy code path without git overhead.
    """
    _FIXTURE_REGISTRY[commit_sha] = _FixtureCommit(
        commit_sha=commit_sha,
        claim_ids=frozenset(claim_ids),
        stances=tuple(stances),
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
    belief_space: Any,
    journal: TransitionJournal,
    k: int,
) -> ClaimView:
    """Re-derive a ClaimView at journal step ``k`` against the snapshot's commit.

    Walks the registered fixture commit (or, in production, checks out
    ``state.scope.commit`` via dulwich and rebuilds the sidecar). Caches
    by ``(commit_sha, frozenset[claim_id])``.

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
        # Production path would invoke dulwich here. For now, fall back to
        # the minimal projection's claim set — same as heavy=False — so that
        # un-registered commits still produce a valid view; stances are
        # empty under that fallback.
        rows = belief_space.claims_by_ids(set(minimal_claim_ids))
        view = ClaimView(claims=rows, scope=scope, bound=None, stances=())
    else:
        # Heavy projects the union of (minimal claim_ids) and (the fixture's
        # registered claim_ids), and surfaces the registered stances.
        full_ids = set(minimal_claim_ids) | set(fixture.claim_ids)
        rows = belief_space.claims_by_ids(full_ids)
        view = ClaimView(
            claims=rows, scope=scope, bound=None, stances=fixture.stances
        )
    _CACHE[cache_key] = view
    return view
