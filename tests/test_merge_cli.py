"""CLI tests for ``pks merge inspect`` / ``pks merge commit``.

Ported from the feature-peak ``test_merge_cli`` onto the rewrite owners:
``merge inspect`` renders :func:`~propstore.merge.summarize_merge_framework` over
:func:`~propstore.merge.build_repository_merge_framework`; ``merge commit`` renders
the :func:`~propstore.app.merge.commit_merge` facade report.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.merge import (
    build_repository_merge_framework,
    summarize_merge_framework,
)
from propstore.repository import Repository
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


def _seed_conflict(
    tmp_path: Path,
    branch: str,
    *,
    master_conditions: tuple[str, ...] = (),
    branch_conditions: tuple[str, ...] = (),
) -> Repository:
    """master/branch each hold a rival value for ``claim1`` over ``concept_x``."""
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "concept_x")
    author_param_claim(repo, "claim1", "concept_x", 250.0)
    base_sha = repo.require_git().branch_sha("master")
    assert base_sha is not None
    repo.require_git().create_branch(branch, source_commit=base_sha)
    author_param_claim(repo, "claim1", "concept_x", 300.0, conditions=master_conditions)
    author_param_claim(
        repo, "claim1", "concept_x", 150.0, branch=branch, conditions=branch_conditions
    )
    return repo


def test_merge_inspect_surfaces_query_summary(tmp_path: Path) -> None:
    branch = "paper/conflict"
    repo = _seed_conflict(tmp_path, branch)

    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "merge", "inspect", "master", branch]
    )
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "formal_merge_report"
    assert payload["framework_type"] == "partial_argumentation_framework"
    assert len(payload["arguments"]) == 2
    assert payload["relation_counts"]["attack"] == 2
    assert payload["relation_counts"]["ignorance"] == 0


def test_merge_inspect_phi_node_reports_ignorance(tmp_path: Path) -> None:
    branch = "paper/phi"
    repo = _seed_conflict(
        tmp_path,
        branch,
        master_conditions=("temp > 300",),
        branch_conditions=("temp < 200",),
    )

    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "merge", "inspect", "master", branch]
    )
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["relation_counts"]["ignorance"] == 2
    assert payload["relation_counts"]["attack"] == 0


def test_merge_inspect_matches_owner_helper(tmp_path: Path) -> None:
    branch = "paper/differential"
    repo = _seed_conflict(tmp_path, branch)
    expected = summarize_merge_framework(
        build_repository_merge_framework(repo, "master", branch),
        semantics="preferred",
    )

    result = CliRunner().invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "merge",
            "inspect",
            "master",
            branch,
            "--semantics",
            "preferred",
        ],
    )
    assert result.exit_code == 0, result.output
    assert yaml.safe_load(result.output) == expected


def test_merge_commit_surfaces_storage_commit_metadata(tmp_path: Path) -> None:
    branch = "paper/storage"
    repo = _seed_conflict(tmp_path, branch)

    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "merge", "commit", "master", branch]
    )
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["surface"] == "storage_merge_commit"
    assert payload["branch_a"] == "master"
    assert payload["branch_b"] == branch
    assert payload["target_branch"] == "master"
    assert len(payload["commit_sha"]) == 40
    assert len(payload["claims_paths"]) == 2
    assert payload["manifest_path"] is not None
    assert payload["manifest_path"].endswith(".yaml")
    assert payload["manifest_path"].startswith("merge_manifest/")
    # The merge commit became the new master HEAD.
    assert repo.require_git().head_sha() == payload["commit_sha"]
