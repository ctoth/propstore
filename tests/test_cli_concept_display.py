"""CLI adapter tests for the ``pks concept`` read-view family (Phase 10-1).

Exercises the thin Click adapters end-to-end through the root ``cli`` lazy
registry against the real owner tier (:mod:`propstore.app.concepts.display`,
:mod:`propstore.app.concept_views`) over the shared Phase 10-0 demo repo.

Ported and adapted from the reference ``test_cli`` concept display cases; concept
``embed`` / ``similar`` (10-3) and any direct concept mutation (no owner) are
deferred and noted in the worker report. The ``align`` / ``decide`` / ``promote``
lifecycle is covered by ``test_concept_alignment_cli``.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner, Result

from tests.app_render_helpers import build_demo_repo
from propstore.cli import cli
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "concept", *args])


def test_list_shows_visible_hides_drafts(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["list"])
    assert result.exit_code == 0, result.output
    assert "speed" in result.output
    assert "draftconcept" not in result.output


def test_list_include_drafts_shows_draft_concept(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["list", "--include-drafts"])
    assert result.exit_code == 0, result.output
    assert "draftconcept" in result.output


def test_search_matches_name(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["search", "spe"])
    assert result.exit_code == 0, result.output
    assert "speed" in result.output


def test_show_renders_concept(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "speed"])
    assert result.exit_code == 0, result.output
    assert "Concept speed" in result.output
    assert "velocity" in result.output


def test_show_json_shape(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "speed", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["concept_id"] == "speed"
    assert data["canonical_name"] == "speed"


def test_show_unknown_concept_fails(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    result = _invoke(repo, ["show", "nope"])
    assert result.exit_code != 0
    assert "Unknown concept: nope" in result.output
