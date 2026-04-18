from __future__ import annotations

from propstore.repository import Repository
from propstore.repository_history import (
    CommitNotFoundError,
    build_commit_show_report,
    build_diff_report,
    checkout_commit,
)


def test_diff_and_show_reports_project_snapshot_history(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add a")
    git.commit_files(
        {
            "concepts/a.yaml": b"v: 2\n",
            "concepts/b.yaml": b"v: 1\n",
        },
        "update files",
    )
    sha = git.head_sha()

    diff = build_diff_report(repo, None)
    shown = build_commit_show_report(repo, sha)

    assert diff.has_changes
    assert diff.added == ("concepts/b.yaml",)
    assert diff.modified == ("concepts/a.yaml",)
    assert shown.sha == sha
    assert shown.message == "update files"
    assert shown.changes.added == ("concepts/b.yaml",)


def test_checkout_report_rejects_missing_commit(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    try:
        checkout_commit(repo, "missing")
    except CommitNotFoundError as exc:
        assert str(exc) == "Commit not found: missing"
    else:
        raise AssertionError("expected missing commit failure")
