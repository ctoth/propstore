from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.heuristic.relate import dedup_pairs


def test_dedup_pairs_preserves_forward_and_reverse_distances() -> None:
    result = dedup_pairs([("a", "b", 0.3), ("b", "a", 0.4)])

    assert result == [("a", "b", 0.3, 0.4)]


@pytest.mark.property
@given(
    forward=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    reverse=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_dedup_pairs_never_replaces_asymmetric_distances_with_minimum(
    forward: float,
    reverse: float,
) -> None:
    result = dedup_pairs([("a", "b", forward), ("b", "a", reverse)])

    assert result == [("a", "b", forward, reverse)]
