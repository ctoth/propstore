"""Property invariants for predicate authoring.

* A predicate id is globally unique regardless of which authoring group / file
  declares it.
* Concurrent same-id adds resolve to exactly one survivor; every loser sees a
  :class:`PredicateWorkflowError` (or a quire ``HeadMismatchError``).
"""

from __future__ import annotations

import threading

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from quire.git_store import HeadMismatchError

from propstore.families.predicates import PredicateRepository
from propstore.grounding.authoring import (
    PredicateAddRequest,
    PredicateWorkflowError,
    add_predicate,
    list_predicates,
)

_IDS = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=12)
_GROUPS = st.lists(st.text(alphabet="abcdef", min_size=1, max_size=5), min_size=1, max_size=5)


@pytest.mark.property
@given(predicate_id=_IDS, groups=_GROUPS)
@settings(max_examples=50, deadline=None)
def test_predicate_id_unique_regardless_of_authoring_group(
    predicate_id: str, groups: list[str]
) -> None:
    repo = PredicateRepository()
    declared = False
    for group in groups:
        if not declared:
            add_predicate(
                repo,
                PredicateAddRequest(predicate_id=predicate_id, arity=0, authoring_group=group),
            )
            declared = True
        else:
            with pytest.raises(PredicateWorkflowError):
                add_predicate(
                    repo,
                    PredicateAddRequest(predicate_id=predicate_id, arity=0, authoring_group=group),
                )
    surviving = [item for item in list_predicates(repo) if item.predicate_id == predicate_id]
    assert len(surviving) == 1


@pytest.mark.property
@given(thread_count=st.integers(min_value=2, max_value=8))
@settings(max_examples=20, deadline=None)
def test_concurrent_same_id_add_has_one_survivor(thread_count: int) -> None:
    repo = PredicateRepository()
    successes: list[int] = []
    losers: list[int] = []
    barrier = threading.Barrier(thread_count)

    def worker(index: int) -> None:
        barrier.wait()
        try:
            add_predicate(
                repo,
                PredicateAddRequest(predicate_id="dup", arity=0, authoring_group=f"g{index}"),
            )
            successes.append(index)
        except (PredicateWorkflowError, HeadMismatchError):
            losers.append(index)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(successes) == 1
    assert len(losers) == thread_count - 1
    surviving = [item for item in list_predicates(repo) if item.predicate_id == "dup"]
    assert len(surviving) == 1
