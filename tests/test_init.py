"""Tests for pks init."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from compiler.cli import cli


@pytest.fixture()
def empty_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty temporary directory with no propstore structure."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestInit:
    def test_creates_default_structure(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output
        assert "Initialized" in result.output

        root = empty_workspace / "knowledge"
        assert (root / "concepts").is_dir()
        assert (root / "concepts" / ".counters").is_dir()
        assert (root / "claims").is_dir()
        assert (root / "sidecar").is_dir()

    def test_creates_at_custom_path(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "myproject"])
        assert result.exit_code == 0, result.output
        assert "myproject" in result.output

        root = empty_workspace / "myproject"
        assert (root / "concepts").is_dir()
        assert (root / "concepts" / ".counters").is_dir()
        assert (root / "claims").is_dir()
        assert (root / "sidecar").is_dir()

    def test_already_initialized(self, empty_workspace: Path) -> None:
        runner = CliRunner()
        # First init
        runner.invoke(cli, ["init", "proj"])
        # Second init — should skip
        result = runner.invoke(cli, ["init", "proj"])
        assert result.exit_code == 0
        assert "Already initialized" in result.output

    def test_validate_after_init(self, empty_workspace: Path) -> None:
        """After init, pks validate should succeed (empty but valid)."""
        runner = CliRunner()
        runner.invoke(cli, ["init", "proj"])

        # pks -C proj validate
        # Since -C requires exists=True and we use CliRunner,
        # we chdir manually and invoke validate directly.
        import os
        os.chdir(empty_workspace / "proj")
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0, result.output

    def test_init_with_directory_flag(self, empty_workspace: Path) -> None:
        """pks -C /some/path init should create knowledge/ inside that path."""
        subdir = empty_workspace / "parent"
        subdir.mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["-C", str(subdir), "init"])
        assert result.exit_code == 0, result.output

        root = subdir / "knowledge"
        assert (root / "concepts").is_dir()
        assert (root / "claims").is_dir()
