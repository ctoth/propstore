from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st
from quire.git_store import HeadMismatchError

from propstore.repository import Repository


_SAFE_NAME = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), min_codepoint=48, max_codepoint=122),
    min_size=1,
    max_size=12,
)
_PAYLOAD = st.binary(min_size=1, max_size=64)


@pytest.mark.property
@given(name=_SAFE_NAME, payload=_PAYLOAD)
def test_ws_q_generated_stale_expected_heads_fail_before_mutation(
    name: str,
    payload: bytes,
) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repository.init(Path(tmp_dir) / "knowledge")
        _assert_stale_expected_head_fails(repo, name=name, payload=payload)


def _assert_stale_expected_head_fails(repo: Repository, *, name: str, payload: bytes) -> None:
    path = f"contexts/{name}.yaml"

    git = repo.git
    assert git is not None
    with git.head_bound_transaction("master") as stale_txn:
        advanced_head = git.commit_batch(
            adds={"contexts/winner.yaml": b"id: winner\nname: Winner\n"},
            deletes=(),
            message="Concurrent winner",
            branch="master",
        )
        with pytest.raises(HeadMismatchError):
            stale_txn.commit_batch(
                adds={path: payload},
                deletes=(),
                message="Stale loser",
            )

    assert repo.git.branch_sha("master") == advanced_head
    with pytest.raises(FileNotFoundError):
        repo.git.read_file(path, commit=advanced_head)


@pytest.mark.property
@given(first=_SAFE_NAME, second=_SAFE_NAME, payload=_PAYLOAD)
def test_ws_q_generated_serialized_operations_both_commit(
    first: str,
    second: str,
    payload: bytes,
) -> None:
    assume(first != second)
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repository.init(Path(tmp_dir) / "knowledge")
        _assert_serialized_writers_both_commit(repo, first=first, second=second, payload=payload)


def _assert_serialized_writers_both_commit(
    repo: Repository,
    *,
    first: str,
    second: str,
    payload: bytes,
) -> None:
    first_path = f"contexts/{first}.yaml"
    second_path = f"contexts/{second}.yaml"
    git = repo.git
    assert git is not None
    first_txn = git.head_bound_transaction("master")
    second_txn = git.head_bound_transaction("master")

    with first_txn:
        first_commit = first_txn.commit_batch(
            adds={first_path: payload},
            deletes=(),
            message="First writer",
        )

    with second_txn:
        assert second_txn.expected_head == first_commit
        second_commit = second_txn.commit_batch(
            adds={second_path: payload},
            deletes=(),
            message="Second writer",
        )

    assert repo.git.branch_sha("master") == second_commit
    assert repo.git.read_file(first_path, commit=second_commit) == payload
    assert repo.git.read_file(second_path, commit=second_commit) == payload
