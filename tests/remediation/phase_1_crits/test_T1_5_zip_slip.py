from __future__ import annotations

from pathlib import Path

import pytest

from propstore.source.promote import sync_source_branch
from quire.git_store import TreeFile


class _EscapingGit:
    def __init__(self, relpath: str) -> None:
        self.relpath = relpath

    def branch_sha(self, name: str) -> str | None:
        return "source-tip"

    def iter_tree_files(self, *, commit: str | None = None, roots=()):
        yield TreeFile(relpath=self.relpath, content=b"payload")


class _Repository:
    def __init__(self, root: Path, relpath: str) -> None:
        self.root = root
        self.git = _EscapingGit(relpath)


@pytest.mark.parametrize(
    "evil_path",
    [
        "../escape.txt",
        "subdir/../../escape.txt",
        "..\\windows-escape.txt",
        "./safe/../../escape.txt",
    ],
)
def test_sync_source_branch_rejects_paths_that_escape_output_dir(
    tmp_path: Path,
    evil_path: str,
) -> None:
    repo = _Repository(tmp_path / "repo", evil_path)
    output_dir = tmp_path / "out"

    with pytest.raises(ValueError, match="path escapes output_dir"):
        sync_source_branch(repo, "paper-one", output_dir=output_dir)  # type: ignore[arg-type]

    assert not (tmp_path / "escape.txt").exists()
    assert not (tmp_path / "windows-escape.txt").exists()
