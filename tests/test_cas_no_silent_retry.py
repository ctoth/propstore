from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from propstore.repository import Repository, StaleHeadError
from tests.test_branch_head_cas_matrix import (
    MutationRunner,
    _advance_branch,
    _finalize_runner,
    _materialize_runner,
    _promote_runner,
    _repository_import_runner,
    _seed_import_source,
    _seed_ready_source_branch,
    _seed_source_branch,
)


@pytest.mark.parametrize(
    ("path_name", "branch", "seed", "runner_factory"),
    [
        ("finalize", "source/race", _seed_source_branch, lambda _tmp: _finalize_runner),
        ("promote", "master", _seed_ready_source_branch, lambda _tmp: _promote_runner),
        (
            "repository_import",
            "import/source-project",
            lambda repo, _source_name: None,
            lambda tmp: _repository_import_runner(_seed_import_source(tmp)),
        ),
        ("materialize", "master", lambda repo, _source_name: None, lambda _tmp: _materialize_runner),
    ],
)
def test_cas_rejection_is_not_silently_retried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_name: str,
    branch: str,
    seed: Callable[[Repository, str], object],
    runner_factory: Callable[[Path], MutationRunner],
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    seed(repo, "race")
    runner = runner_factory(tmp_path)
    if branch.startswith("import/"):
        repo.snapshot.ensure_branch(branch)
    head_at_start = repo.snapshot.branch_head(branch)
    assert head_at_start is not None
    attempts = 0

    if path_name == "materialize":
        original_files = repo.snapshot.files

        def files_and_race(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            result = original_files(*args, **kwargs)
            _advance_branch(repo, branch)
            return result

        monkeypatch.setattr(repo.snapshot, "files", files_and_race)
    else:
        original_commit_batch = type(repo.git).commit_batch

        def stale_once_then_succeed(self, adds, deletes, message, *, branch=None, expected_head=None):
            nonlocal attempts
            if branch == target_branch and expected_head == head_at_start:
                attempts += 1
                if attempts == 1:
                    raise ValueError(
                        f"Branch {branch!r} head mismatch: expected {expected_head}, got concurrent-head"
                    )
            return original_commit_batch(
                self,
                adds,
                deletes,
                message,
                branch=branch,
                expected_head=expected_head,
            )

        target_branch = branch
        monkeypatch.setattr(type(repo.git), "commit_batch", stale_once_then_succeed)

    with pytest.raises(StaleHeadError):
        runner(repo)

    assert attempts == 1
