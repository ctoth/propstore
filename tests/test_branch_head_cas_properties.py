from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st

from propstore.repository import Repository, StaleHeadError


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

    with repo.head_bound_transaction("master", path="property") as stale_txn:
        advanced_head = repo.git.commit_batch(
            adds={"contexts/winner.yaml": b"id: winner\nname: Winner\n"},
            deletes=(),
            message="Concurrent winner",
            branch="master",
        )
        with pytest.raises(StaleHeadError):
            stale_txn.commit_batch(
                adds={path: payload},
                deletes=(),
                message="Stale loser",
            )

    assert repo.snapshot.branch_head("master") == advanced_head
    with pytest.raises(FileNotFoundError):
        repo.git.read_file(path, commit=advanced_head)


@pytest.mark.property
@given(first=_SAFE_NAME, second=_SAFE_NAME, payload=_PAYLOAD)
def test_ws_q_generated_concurrent_operations_have_one_winner(
    first: str,
    second: str,
    payload: bytes,
) -> None:
    assume(first != second)
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repository.init(Path(tmp_dir) / "knowledge")
        _assert_one_concurrent_writer_wins(repo, first=first, second=second, payload=payload)


def _assert_one_concurrent_writer_wins(
    repo: Repository,
    *,
    first: str,
    second: str,
    payload: bytes,
) -> None:
    first_path = f"contexts/{first}.yaml"
    second_path = f"contexts/{second}.yaml"
    first_txn = repo.head_bound_transaction("master", path="property")
    second_txn = repo.head_bound_transaction("master", path="property")

    with first_txn:
        winner = first_txn.commit_batch(
            adds={first_path: payload},
            deletes=(),
            message="First writer wins",
        )

    with pytest.raises(StaleHeadError):
        with second_txn:
            second_txn.commit_batch(
                adds={second_path: payload},
                deletes=(),
                message="Second writer loses",
            )

    assert repo.snapshot.branch_head("master") == winner
    assert repo.git.read_file(first_path, commit=winner) == payload
    with pytest.raises(FileNotFoundError):
        repo.git.read_file(second_path, commit=winner)
