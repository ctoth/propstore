"""CLI tests for ``pks init`` (the Click adapter over ``initialize_project``)."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository


def _visible_paths(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if ".git" not in path.relative_to(root).parts
    }


@pytest.fixture()
def empty_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_init_creates_store_only_repository(empty_workspace: Path) -> None:
    result = CliRunner().invoke(cli, ["init"])
    assert result.exit_code == 0, result.output
    assert "Initialized" in result.output

    root = empty_workspace / "knowledge"
    assert (root / ".git").is_dir()
    # Store-only: no loose semantic directories are materialized.
    assert not (root / "concepts").exists()
    assert not (root / "concept").exists()
    assert _visible_paths(root) == set()
    # But the seed is committed to the store.
    repo = Repository.find(root)
    assert repo.families.concept.load("ps:concept:measurement") is not None


def test_init_creates_at_custom_path(empty_workspace: Path) -> None:
    result = CliRunner().invoke(cli, ["init", "myproject"])
    assert result.exit_code == 0, result.output
    assert "myproject" in result.output

    root = empty_workspace / "myproject"
    assert (root / ".git").is_dir()
    assert (
        Repository.find(root).families.concept.load("ps:concept:measurement")
        is not None
    )


def test_init_already_initialized_is_idempotent(empty_workspace: Path) -> None:
    runner = CliRunner()
    runner.invoke(cli, ["init", "proj"])
    result = runner.invoke(cli, ["init", "proj"])
    assert result.exit_code == 0, result.output
    assert "Already initialized" in result.output


def test_init_with_directory_flag(empty_workspace: Path) -> None:
    """``pks -C PARENT init`` creates ``knowledge/`` inside PARENT."""
    parent = empty_workspace / "parent"
    parent.mkdir()

    result = CliRunner().invoke(cli, ["-C", str(parent), "init"])
    assert result.exit_code == 0, result.output

    root = parent / "knowledge"
    assert (root / ".git").is_dir()
    assert (
        Repository.find(root).families.concept.load("ps:concept:measurement")
        is not None
    )


def test_init_validate_after_init(empty_workspace: Path) -> None:
    runner = CliRunner()
    runner.invoke(cli, ["init", "proj"])
    result = runner.invoke(cli, ["-C", str(empty_workspace / "proj"), "validate"])
    assert result.exit_code == 0, result.output
