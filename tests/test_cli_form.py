"""CLI adapter tests for the ``pks form`` read-view family (Phase 10-1).

The rewrite owner layer exposes only :func:`propstore.app.forms.show_form`, so the
adapter (and these tests) cover ``form show`` only; ``form list`` / ``search`` /
``add`` / ``remove`` / ``validate`` have no rewrite owner and are deferred.
"""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from tests.app_render_helpers import build_demo_repo
from propstore.cli import cli
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "form", *args])


def test_show_renders_form_yaml(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "velocity"])
    assert result.exit_code == 0, result.output
    assert "velocity" in result.output


def test_show_unknown_form_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
