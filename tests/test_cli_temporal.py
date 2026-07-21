"""CLI adapter smoke tests for ``pks temporal``.

Drives the production path end to end through the CLI: author frames/anchors/
edges, then render the recomputed happens-before order with its witnessing
evidence path.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result

from propstore.cli import cli
from propstore.repository import Repository


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "temporal", *args])


def test_author_and_order_renders_verdict_and_path(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)

    assert _invoke(repo, ["edge", "c1", "c2", "--edge-id", "e1", "--account", "message"]).exit_code == 0
    assert _invoke(repo, ["edge", "c2", "c3", "--edge-id", "e2", "--account", "message"]).exit_code == 0

    result = _invoke(repo, ["order", "c1", "c3"])
    assert result.exit_code == 0, result.output
    assert "Verdict: before" in result.output
    assert "c1 -> c2 [authored_posit account=message edge=e1]" in result.output
    assert "c2 -> c3 [authored_posit account=message edge=e2]" in result.output


def test_frame_and_anchor_author_and_prove_concurrency(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)

    assert _invoke(repo, ["frame", "--frame-id", "f1", "--description", "clock"]).exit_code == 0
    assert _invoke(
        repo,
        ["anchor", "--anchor-id", "a1", "--claim-id", "c1", "--frame-id", "f1", "--valid-from", "0", "--valid-until", "10"],
    ).exit_code == 0
    assert _invoke(
        repo,
        ["anchor", "--anchor-id", "a2", "--claim-id", "c2", "--frame-id", "f1", "--valid-from", "5", "--valid-until", "15"],
    ).exit_code == 0

    result = _invoke(repo, ["order", "c1", "c2"])
    assert result.exit_code == 0, result.output
    assert "Verdict: concurrent_proven" in result.output
    assert "Concurrency proven by frame: f1" in result.output


def test_stated_edges_do_not_chain_in_cli(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    assert _invoke(repo, ["edge", "c1", "c2", "--edge-id", "e1", "--account", "stated"]).exit_code == 0
    assert _invoke(repo, ["edge", "c2", "c3", "--edge-id", "e2", "--account", "stated"]).exit_code == 0

    result = _invoke(repo, ["order", "c1", "c3"])
    assert result.exit_code == 0, result.output
    assert "Verdict: unknown" in result.output
