from __future__ import annotations

import threading

from propstore.concept_ids import next_concept_id_for_repo
from propstore.repository import Repository


def test_concurrent_concept_id_allocation_reserves_unique_ids(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    barrier = threading.Barrier(8)
    lock = threading.Lock()
    allocated: list[int] = []
    errors: list[BaseException] = []

    def allocate() -> None:
        try:
            barrier.wait()
            numeric_id = next_concept_id_for_repo(repo)
            with lock:
                allocated.append(numeric_id)
        except BaseException as exc:  # pragma: no cover - surfaced below
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=allocate) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(allocated) == 8
    assert len(set(allocated)) == 8
    assert min(allocated) >= 1
