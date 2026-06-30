"""CLI adapter tests for the ``pks context`` read-view family (Phase 10-1).

Contexts are immutable except through the source subsystem and have no rewrite app
owner, so the adapter (and these tests) cover the two read projections over the
context family store — ``context list`` and ``context show`` — only. Authoring
(``add`` / ``remove`` / lifting-rule) is deferred until a context owner lands.
"""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from tests.app_render_helpers import build_demo_repo
from propstore.cli import cli
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "context", *args])


def test_list_shows_stored_context(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["list"])
    assert result.exit_code == 0, result.output
    assert "ctx1" in result.output


def test_show_renders_context(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "ctx1"])
    assert result.exit_code == 0, result.output
    assert "ctx1" in result.output


def test_show_unknown_context_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
