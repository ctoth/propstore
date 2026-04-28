from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from propstore.repository import Repository, StaleHeadError


def test_head_bound_transaction_captures_head_and_threads_expected_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    captured_head = repo.snapshot.branch_head("master")
    seen: list[tuple[str | None, str | None]] = []
    original_commit_batch = type(repo.git).commit_batch

    def commit_batch_spy(self, adds, deletes, message, *, branch=None, expected_head=None):
        seen.append((branch, expected_head))
        return original_commit_batch(
            self,
            adds,
            deletes,
            message,
            branch=branch,
            expected_head=expected_head,
        )

    monkeypatch.setattr(type(repo.git), "commit_batch", commit_batch_spy)

    with repo.head_bound_transaction("master") as txn:
        assert txn.expected_head == captured_head
        with pytest.raises(FrozenInstanceError):
            txn.expected_head = "not-the-captured-head"
        txn.commit_batch(
            adds={"contexts/demo.yaml": b"id: demo\nname: Demo\n"},
            deletes=(),
            message="Write demo context",
        )

    assert seen == [("master", captured_head)]


def test_head_bound_transaction_flushes_sidecar_writes_only_after_commit(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    applied: list[str | None] = []

    with repo.head_bound_transaction("master") as txn:
        txn.sidecar_write(lambda: applied.append(txn.commit_sha))
        assert applied == []
        txn.commit_batch(
            adds={"contexts/demo.yaml": b"id: demo\nname: Demo\n"},
            deletes=(),
            message="Write demo context",
        )

    assert applied == [repo.snapshot.branch_head("master")]


def test_head_bound_transaction_discards_sidecar_writes_on_stale_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    captured_head = repo.snapshot.branch_head("master")
    applied: list[str] = []

    def stale_commit_batch(self, adds, deletes, message, *, branch=None, expected_head=None):
        raise ValueError(
            f"Branch {branch!r} head mismatch: expected {expected_head}, got newer-head"
        )

    monkeypatch.setattr(type(repo.git), "commit_batch", stale_commit_batch)

    with pytest.raises(StaleHeadError) as exc_info:
        with repo.head_bound_transaction("master") as txn:
            txn.sidecar_write(lambda: applied.append("sidecar-write-leaked"))
            txn.commit_batch(
                adds={"contexts/demo.yaml": b"id: demo\nname: Demo\n"},
                deletes=(),
                message="Write demo context",
            )

    assert exc_info.value.branch == "master"
    assert exc_info.value.expected_head == captured_head
    assert exc_info.value.actual_head == "newer-head"
    assert applied == []
