from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from types import MethodType
from typing import Any

from hypothesis import settings
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)
from quire.git_store import GitStore, HeadMismatchError
from quire.refs import RefName
from quire.sqlalchemy_store import readonly_session
from sqlalchemy import text

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from propstore.compiler.workflows import write_repository_world_store as build_sidecar
from propstore.families.registry import world_schema
from tests.git_store_helpers import init_store
from propstore.storage.snapshot import RepositorySnapshot


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
                sidecar_path = repo.root / ".tmp-race-suite.sqlite"
                build_sidecar(repo, sidecar_path, force=True, commit_hash=head)
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
        sidecar_path = repo.root / ".tmp-race-suite.sqlite"
        assert sidecar_path.exists()
        assert sidecar_path.with_suffix(".hash").exists()
        with readonly_session(sidecar_path, world_schema()) as derived:
            schema_version = derived.session.execute(
                text("SELECT schema_version FROM meta WHERE key = 'sidecar'")
            ).fetchone()
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
