from __future__ import annotations

import threading
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.app.predicates import (
    PredicateAddRequest,
    PredicateWorkflowError,
    add_predicate,
)
from propstore.grounding.predicates import PredicateRegistry
from propstore.repository import Repository, StaleHeadError


_NAME = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)


def _predicate_ids(repo: Repository) -> list[str]:
    ids: list[str] = []
    for handle in repo.families.predicates.iter_handles():
        for predicate in handle.document.predicates:
            ids.append(predicate.id)
    return ids


@pytest.mark.property
@given(
    first_file=_NAME,
    second_file=_NAME,
    predicate_id=_NAME,
)
@settings(deadline=None, max_examples=20)
def test_generated_predicate_add_rejects_global_duplicate_ids(
    first_file: str,
    second_file: str,
    predicate_id: str,
) -> None:
    if first_file == second_file:
        second_file = f"{second_file}_other"
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        repo = Repository.init(Path(tmp_dir.name) / "knowledge")

        add_predicate(
            repo,
            PredicateAddRequest(file=first_file, predicate_id=predicate_id, arity=1),
        )

        with pytest.raises(PredicateWorkflowError, match="already declared"):
            add_predicate(
                repo,
                PredicateAddRequest(file=second_file, predicate_id=predicate_id, arity=1),
            )

        assert _predicate_ids(repo).count(predicate_id) == 1
        PredicateRegistry.from_files(
            tuple(handle.document for handle in repo.families.predicates.iter_handles())
        )


@pytest.mark.property
@given(
    first_file=_NAME,
    second_file=_NAME,
    predicate_id=_NAME,
)
@settings(deadline=None, max_examples=10)
def test_generated_concurrent_predicate_adds_do_not_leave_duplicate_ids(
    first_file: str,
    second_file: str,
    predicate_id: str,
) -> None:
    if first_file == second_file:
        second_file = f"{second_file}_other"
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        barrier = threading.Barrier(2)
        outcomes: list[str] = []
        lock = threading.Lock()

        def add_in_thread(file_name: str) -> None:
            local_repo = Repository(repo.root)
            barrier.wait(timeout=5)
            try:
                add_predicate(
                    local_repo,
                    PredicateAddRequest(file=file_name, predicate_id=predicate_id, arity=1),
                )
            except (PredicateWorkflowError, StaleHeadError) as exc:
                with lock:
                    outcomes.append(type(exc).__name__)
                return
            with lock:
                outcomes.append("success")

        threads = (
            threading.Thread(target=add_in_thread, args=(first_file,)),
            threading.Thread(target=add_in_thread, args=(second_file,)),
        )
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert len(outcomes) == 2
        assert outcomes.count("success") == 1
        assert _predicate_ids(repo).count(predicate_id) == 1
        PredicateRegistry.from_files(
            tuple(handle.document for handle in repo.families.predicates.iter_handles())
        )
