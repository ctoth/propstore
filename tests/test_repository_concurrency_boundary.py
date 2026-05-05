from __future__ import annotations

import threading
from pathlib import Path

from propstore.repository import Repository


def test_head_bound_transactions_serialize_head_capture_and_commit(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    initial_head = repo.snapshot.branch_head("master")
    assert initial_head is not None

    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    first_done = threading.Event()
    second_done = threading.Event()
    failures: list[BaseException] = []
    observed_heads: dict[str, str | None] = {}
    commits: dict[str, str] = {}

    def first_writer() -> None:
        try:
            with repo.head_bound_transaction("master", path="first") as txn:
                observed_heads["first"] = txn.expected_head
                first_entered.set()
                release_first.wait(timeout=5)
                commits["first"] = txn.commit_batch(
                    adds={"contexts/first.yaml": b"id: first\nname: First\n"},
                    deletes=(),
                    message="First writer",
                )
        except BaseException as exc:
            failures.append(exc)
        finally:
            first_done.set()

    def second_writer() -> None:
        try:
            first_entered.wait(timeout=5)
            with repo.head_bound_transaction("master", path="second") as txn:
                second_entered.set()
                observed_heads["second"] = txn.expected_head
                commits["second"] = txn.commit_batch(
                    adds={"contexts/second.yaml": b"id: second\nname: Second\n"},
                    deletes=(),
                    message="Second writer",
                )
        except BaseException as exc:
            failures.append(exc)
        finally:
            second_done.set()

    first_thread = threading.Thread(target=first_writer)
    second_thread = threading.Thread(target=second_writer)
    first_thread.start()
    assert first_entered.wait(timeout=5)
    second_thread.start()
    assert not second_entered.wait(timeout=0.1)

    release_first.set()
    assert first_done.wait(timeout=5)
    assert second_done.wait(timeout=5)
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert failures == []
    assert observed_heads["first"] == initial_head
    assert observed_heads["second"] == commits["first"]
    assert repo.snapshot.branch_head("master") == commits["second"]
    assert repo.git.read_file("contexts/first.yaml", commit=commits["second"])
    assert repo.git.read_file("contexts/second.yaml", commit=commits["second"])
