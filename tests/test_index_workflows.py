"""Tests for the ``pks index reset`` workflow."""

from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from propstore.index_workflows import reset_index
from propstore.repository import Repository


def _stage_phantom_entry(repo: Repository, relpath: str) -> None:
    """Insert a fake index entry pointing at a non-existent path.

    Mirrors the real-world sequence in
    ``feedback_propstore_git_backend.md``: a user's index holds entries
    for files that are not in the propstore-authored tree. A later
    commit would carry those entries into the commit tree. The exact
    shape of the entry does not matter for this test — what matters is
    that ``reset_index`` rewrites the index to match HEAD, dropping
    whatever was there.
    """
    from dulwich.index import Index, IndexEntry

    git = repo.git
    dulwich_repo = git._repo  # type: ignore[attr-defined]
    index = Index(dulwich_repo.index_path())
    entry = IndexEntry(
        ctime=(0, 0),
        mtime=(0, 0),
        dev=0,
        ino=0,
        mode=0o100644,
        uid=0,
        gid=0,
        size=0,
        sha=b"0" * 40,
        flags=0,
    )
    index[relpath.encode("utf-8")] = entry
    index.write()


def test_reset_index_rewrites_to_head(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    # Establish an ordinary commit so HEAD has a tree we can reset to.
    repo.git.commit_files({"claims/foo.yaml": b"claims: []\n"}, "seed claims")

    _stage_phantom_entry(repo, "claims/ghost.yaml")

    report = reset_index(repo)

    assert isinstance(report.head_sha, str)
    assert len(report.head_sha) == 40

    # After reset, the phantom entry must be gone.
    from dulwich.index import Index

    dulwich_repo = repo.git._repo  # type: ignore[attr-defined]
    index = Index(dulwich_repo.index_path())
    assert b"claims/ghost.yaml" not in {
        (path if isinstance(path, bytes) else path.encode()) for path in index
    }


def test_index_cli_reset(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files({"concepts/seed.yaml": b"canonical_name: seed\n"}, "seed")

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(repo.root), "index", "reset"])

    assert result.exit_code == 0, result.output
    assert "Reset index to HEAD" in result.output
