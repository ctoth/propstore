"""Tests for BoundWorld caching of conflict-detection registry inputs.

Regression guard for Defect 4: `_conflict_inputs_for_store` was rebuilt on
every `BoundWorld.conflicts(concept_id)` invocation, so two calls with
distinct concept ids paid the full iterate-all-concepts cost twice. The
registry inputs are invariant for the lifetime of a `BoundWorld` instance
(since `BoundWorld._store` is set once in `__init__` and never rebound), so
they must be memoised on the instance.

Overlay safety note: the free function `_conflict_inputs_for_store` is ALSO
called by `propstore.world.hypothetical` against a `_GraphOverlayStore`.
Those call sites must continue to rebuild — a shared cache would validate
synthetic overlay claims against the base store's registry. This test only
asserts caching WITHIN a single `BoundWorld` instance; it does not (and
must not) require caching across the base/overlay boundary.
"""

from unittest.mock import Mock

import pytest

import propstore.world.bound as bound_module
from tests.test_world_model import (
    CONCEPT1_ID,
    CONCEPT2_ID,
    claim_files,
    concept_dir,
    repo,
    world,
)


class TestBoundConflictInputsCache:
    def test_conflict_inputs_built_once_across_concept_calls(self, world, monkeypatch):
        """Two .conflicts() calls with distinct concept ids must rebuild the
        concept+CEL registry exactly once — the inputs depend only on
        `self._store`, which is immutable over a BoundWorld's lifetime.
        """
        bound = world.bind(task="speech")

        real_builder = bound_module._conflict_inputs_for_store
        wrapped = Mock(wraps=real_builder)
        monkeypatch.setattr(
            bound_module,
            "_conflict_inputs_for_store",
            wrapped,
        )

        # Both concepts have active claims under task=speech and are known
        # to surface conflicts (see TestBoundConflicts::test_speech_has_*).
        first = bound.conflicts(CONCEPT1_ID)
        second = bound.conflicts(CONCEPT2_ID)

        # Sanity: both calls actually exercised the recomputed-conflicts
        # code path (otherwise the cache assertion would be vacuous).
        assert first is not None
        assert second is not None

        # The defect: call_count == 2 on master. After the fix: == 1.
        assert wrapped.call_count == 1, (
            f"Expected _conflict_inputs_for_store to be called once across two "
            f"BoundWorld.conflicts() invocations on distinct concept ids, "
            f"but was called {wrapped.call_count} times."
        )

    def test_repeated_same_concept_call_does_not_rebuild_inputs(self, world, monkeypatch):
        """A second call for the SAME concept id hits `_conflicts_cache`
        directly and never reaches `_recomputed_conflicts`, so the input
        builder still must have been called at most once overall.
        """
        bound = world.bind(task="speech")

        real_builder = bound_module._conflict_inputs_for_store
        wrapped = Mock(wraps=real_builder)
        monkeypatch.setattr(
            bound_module,
            "_conflict_inputs_for_store",
            wrapped,
        )

        bound.conflicts(CONCEPT1_ID)
        bound.conflicts(CONCEPT2_ID)
        bound.conflicts(CONCEPT1_ID)  # cache hit on _conflicts_cache

        assert wrapped.call_count == 1

    def test_hypothetical_overlay_does_not_share_base_conflict_inputs(self, world):
        """Overlay safety guard: the base BoundWorld's conflict-inputs cache
        must NOT be visible to a HypotheticalWorld overlay. The overlay
        wraps a separate `_GraphOverlayStore` and constructs its own fresh
        `BoundWorld`, which has its own independent cache.
        """
        from propstore.world import HypotheticalWorld

        base = world.bind(task="speech")
        # Prime the base cache.
        base.conflicts(CONCEPT1_ID)

        hypo = HypotheticalWorld(base)

        # The overlay's internal BoundWorld is a distinct instance with its
        # own _conflict_inputs_cache. Calling conflicts() on the overlay
        # must not crash and must not corrupt the base.
        _ = hypo.conflicts(CONCEPT1_ID)

        # Base cache still works after the overlay query.
        again = base.conflicts(CONCEPT1_ID)
        assert again is not None
