from __future__ import annotations

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.world.types import QueryableAssumption

from tests.test_atms_engine import _ATMSStore, _make_bound


def test_iter_future_queryable_sets_returns_enumeration_exceeded_past_ceiling() -> None:
    engine = _make_bound(_ATMSStore(claims=[])).atms_engine()
    queryables = [
        QueryableAssumption.from_cel("b == 2"),
        QueryableAssumption.from_cel("a == 1"),
    ]

    result = engine._iter_future_queryable_sets(
        queryables,
        limit=8,
        max_candidates=1,
    )

    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1
    assert result.max_candidates == 1
    assert result.remainder_provenance == ProvenanceStatus.VACUOUS
