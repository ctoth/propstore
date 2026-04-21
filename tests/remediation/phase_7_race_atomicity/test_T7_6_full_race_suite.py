from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from types import MethodType
from typing import Any

import yaml
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule, run_state_machine_as_test
from quire.git_store import GitStore
from quire.refs import RefName

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from propstore.sidecar.sqlite import connect_sidecar
from propstore.storage import init_git_store
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload


def _claim_yaml(claim_id: str, statement: str) -> bytes:
    payload = normalize_claims_payload({
        "source": {
            "paper": "race-suite",
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": [
            {
                "id": claim_id,
                "type": "observation",
                "statement": statement,
                "concepts": [f"concept_{claim_id}"],
                "provenance": {"paper": "race-suite", "page": 1},
            }
        ],
    })
    return yaml.dump(payload, sort_keys=False).encode()


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


class FullRaceMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self._tempdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tempdir.name)
        self._counter = 0
        self._operation_errors: list[BaseException] = []

    def teardown(self) -> None:
        self._tempdir.cleanup()

    def _next_path(self, name: str) -> Path:
        self._counter += 1
        return self._root / f"{self._counter:03d}-{name}"

    @rule()
    def concurrent_merges_guard_target_head(self) -> None:
        kr = init_git_store(self._next_path("merge"))
        base_sha = kr.commit_files({"claims/base.yaml": _claim_yaml("base", "Base")}, "seed")
        branch_name = "paper/race"
        kr.create_branch(branch_name, source_commit=base_sha)
        kr.commit_files({"claims/left.yaml": _claim_yaml("left", "Left")}, "left")
        kr.commit_files(
            {"claims/right.yaml": _claim_yaml("right", "Right")},
            "right",
            branch=branch_name,
        )
        snapshot = _snapshot(kr)
        snapshot_git = snapshot.git
        commit_barrier = threading.Barrier(2)
        original_commit_flat_tree = snapshot_git.commit_flat_tree

        def racing_commit_flat_tree(_self: GitStore, *args: Any, **kwargs: Any) -> str:
            commit_barrier.wait(timeout=5)
            return original_commit_flat_tree(*args, **kwargs)

        snapshot_git.commit_flat_tree = MethodType(racing_commit_flat_tree, snapshot_git)  # type: ignore[method-assign]

        successes: list[str] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def merge_once() -> None:
            try:
                merge_sha = create_merge_commit(snapshot, "master", branch_name)
                with lock:
                    successes.append(merge_sha)
            except BaseException as exc:  # pragma: no cover - surfaced below
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=merge_once) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert not any(thread.is_alive() for thread in threads)
        assert len(successes) == 1, [repr(error) for error in errors]
        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
        assert "head mismatch" in str(errors[0])
        assert kr.branch_sha("master") == successes[0]

    @rule()
    def concurrent_ref_writes_converge_to_written_object(self) -> None:
        store = GitStore.init(self._next_path("refs"))
        left = store.store_blob(b"left")
        right = store.store_blob(b"right")
        ref = RefName("refs/generated/race-suite")
        barrier = threading.Barrier(2)
        errors: list[BaseException] = []
        lock = threading.Lock()

        def write_once(sha: str) -> None:
            try:
                barrier.wait(timeout=5)
                store.write_ref(ref, sha)
            except BaseException as exc:  # pragma: no cover - surfaced below
                with lock:
                    errors.append(exc)

        threads = [
            threading.Thread(target=write_once, args=(left,)),
            threading.Thread(target=write_once, args=(right,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert not any(thread.is_alive() for thread in threads)
        assert all(isinstance(error, ValueError) for error in errors), [
            repr(error) for error in errors
        ]
        assert store.read_ref(ref) in {left, right}

    @rule()
    def concurrent_sidecar_builds_leave_readable_sidecar(self) -> None:
        repo = Repository.init(self._next_path("sidecar"))
        git = repo.git
        if git is None:
            raise AssertionError("race-suite repository must be git-backed")
        head = git.head_sha()
        if head is None:
            raise AssertionError("race-suite repository must have an initial commit")

        barrier = threading.Barrier(2)
        errors: list[BaseException] = []
        lock = threading.Lock()

        def build_once() -> None:
            try:
                barrier.wait(timeout=5)
                build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=head)
            except BaseException as exc:  # pragma: no cover - surfaced below
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=build_once) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
        assert repo.sidecar_path.exists()
        assert repo.sidecar_path.with_suffix(".hash").exists()
        conn = connect_sidecar(repo.sidecar_path)
        try:
            schema_version = conn.execute(
                "SELECT schema_version FROM meta WHERE key = 'sidecar'"
            ).fetchone()
        finally:
            conn.close()
        assert schema_version is not None

    @invariant()
    def no_operation_errors_escaped(self) -> None:
        assert self._operation_errors == []


def test_full_race_suite_covers_merge_ref_and_sidecar_atomicity() -> None:
    """Stateful aggregate for T7.6 race/atomicity surfaces."""
    run_state_machine_as_test(
        FullRaceMachine,
        settings=settings(max_examples=2, stateful_step_count=3, deadline=None),
    )
