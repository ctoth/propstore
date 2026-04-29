"""Tests for pair deduplication in relate module.

Verifies that unordered pair dedup preserves coverage and picks shortest distance.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# The dedup function under test (extracted for testability)
# ---------------------------------------------------------------------------

def _dedup_pairs(pairs: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
    """Deduplicate (a, b, dist) pairs by unordered key, keeping shortest distance.

    This is a test-local copy; the real logic will be inlined in _relate_all_async.
    We test the algorithm here, then verify it's wired in via integration.
    """
    from propstore.heuristic.relate import dedup_pairs
    return dedup_pairs(pairs)


# ---------------------------------------------------------------------------
# Example tests
# ---------------------------------------------------------------------------

class TestDedupRemovesMirrorPairs:
    def test_ab_ba_deduplicates_to_one(self):
        pairs = [("A", "B", 0.3), ("B", "A", 0.5)]
        result = _dedup_pairs(pairs)
        assert len(result) == 1

    def test_surviving_pair_has_shortest_distance(self):
        pairs = [("A", "B", 0.5), ("B", "A", 0.3)]
        result = _dedup_pairs(pairs)
        assert result[0][2] == 0.3


class TestDedupPreservesUniquePairs:
    def test_different_pairs_kept(self):
        pairs = [("A", "B", 0.3), ("A", "C", 0.4)]
        result = _dedup_pairs(pairs)
        assert len(result) == 2


class TestDedupKeepsShortestDistance:
    def test_three_duplicates_keeps_minimum(self):
        pairs = [("X", "Y", 0.7), ("Y", "X", 0.2), ("X", "Y", 0.5)]
        result = _dedup_pairs(pairs)
        assert len(result) == 1
        assert result[0][2] == 0.2


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------

# Strategy: pairs of short string IDs with distances
pair_strategy = st.lists(
    st.tuples(
        st.text(alphabet="ABCDE", min_size=1, max_size=2),
        st.text(alphabet="ABCDE", min_size=1, max_size=2),
        st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
    ),
    min_size=0,
    max_size=50,
)


class TestDedupCountInvariant:
    """After dedup, count equals number of distinct unordered pairs."""

    @pytest.mark.property
    @given(pairs=pair_strategy)
    @settings(max_examples=100)
    def test_count_equals_distinct_frozensets(self, pairs):
        # Filter out self-pairs (a == b) since those aren't meaningful
        pairs = [(a, b, d) for a, b, d in pairs if a != b]
        result = _dedup_pairs(pairs)
        expected_count = len({frozenset({a, b}) for a, b, _ in pairs})
        assert len(result) == expected_count


class TestDedupCoverageInvariant:
    """Every frozenset in input has exactly one representative in output."""

    @pytest.mark.property
    @given(pairs=pair_strategy)
    @settings(max_examples=100)
    def test_every_pair_represented(self, pairs):
        pairs = [(a, b, d) for a, b, d in pairs if a != b]
        result = _dedup_pairs(pairs)
        input_keys = {frozenset({a, b}) for a, b, _ in pairs}
        output_keys = {frozenset({a, b}) for a, b, _ in result}
        assert input_keys == output_keys


class TestDedupMinDistanceInvariant:
    """For each surviving pair, distance is the minimum across all duplicates."""

    @pytest.mark.property
    @given(pairs=pair_strategy)
    @settings(max_examples=100)
    def test_distance_is_minimum(self, pairs):
        pairs = [(a, b, d) for a, b, d in pairs if a != b]
        result = _dedup_pairs(pairs)

        # Build expected min distances
        min_dists: dict[frozenset[str], float] = {}
        for a, b, d in pairs:
            key = frozenset({a, b})
            if key not in min_dists or d < min_dists[key]:
                min_dists[key] = d

        for a, b, d in result:
            key = frozenset({a, b})
            assert d == min_dists[key], f"Expected min distance {min_dists[key]} for {key}, got {d}"
