"""CLI tests for ``pks materialize`` (adapter over ``materialize_repository``)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli
from propstore.families.concepts import Concept
from propstore.repository import Repository


def _repo_with_concept(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    return repo


def test_materialize_projects_loose_files(tmp_path: Path) -> None:
    repo = _repo_with_concept(tmp_path)

    result = CliRunner().invoke(cli, ["-C", str(repo.root), "materialize"])
    assert result.exit_code == 0, result.output
    assert "Materialized" in result.output
    assert "written" in result.output
    # The concept is now a loose source file on disk.
    assert list((repo.root / "concept").glob("*.yaml"))


def test_materialize_commit_and_branch_mutually_exclusive(tmp_path: Path) -> None:
    repo = _repo_with_concept(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["-C", str(repo.root), "materialize", "--commit", "abc", "--branch", "master"],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_materialize_clean_removes_stale_files(tmp_path: Path) -> None:
    repo = _repo_with_concept(tmp_path)
    CliRunner().invoke(cli, ["-C", str(repo.root), "materialize"])
    stale = repo.root / "concept" / "stale.yaml"
    stale.write_bytes(b"stale\n")

    result = CliRunner().invoke(cli, ["-C", str(repo.root), "materialize", "--clean"])
    assert result.exit_code == 0, result.output
    assert not stale.exists()
