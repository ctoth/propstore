"""CLI tests for ``pks log`` / ``diff`` / ``show`` / ``checkout``.

Ported from the feature-peak ``test_log_cli`` onto the rewrite owner API
(:mod:`propstore.history`): the adapters render the typed reports and the YAML
form is the recursively-lowered report.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from tests.merge_commit_helpers import author_concept, author_obs_claim, init_repo


def test_log_output(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    git.commit_files(
        {"concepts/a.yaml": b"canonical_name: alpha\n"},
        "Add concept: alpha (testing:alpha)",
    )

    result = CliRunner().invoke(cli, ["-C", str(root), "log"])
    assert result.exit_code == 0, result.output
    assert "[master]" in result.output
    assert "concept.add" in result.output
    assert "Add concept: alpha" in result.output


def test_log_branch_output(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    git.create_branch("agent/demo")
    git.commit_files(
        {"concepts/agent_demo.yaml": b"canonical_name: agent_demo\n"},
        "Add concept: agent_demo (testing:agent_demo)",
        branch="agent/demo",
    )

    result = CliRunner().invoke(
        cli, ["-C", str(root), "log", "--branch", "agent/demo", "-n", "1"]
    )
    assert result.exit_code == 0, result.output
    assert "[agent/demo]" in result.output
    assert "concept.add" in result.output
    assert "agent_demo" in result.output


def test_log_show_files_output(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add a")
    git.commit_files(
        {"concepts/a.yaml": b"v: 2\n", "concepts/b.yaml": b"v: 1\n"},
        "update files",
    )
    git.commit_deletes(["concepts/a.yaml"], "delete a")

    result = CliRunner().invoke(
        cli, ["-C", str(root), "log", "-n", "2", "--show-files"]
    )
    assert result.exit_code == 0, result.output
    assert "D concepts/a.yaml" in result.output
    assert "A concepts/b.yaml" in result.output
    assert "M concepts/a.yaml" in result.output


def test_log_yaml_output(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    git.commit_files(
        {"concepts/log_yaml.yaml": b"canonical_name: log_yaml\n"},
        "Add concept: log_yaml (testing:log_yaml)",
    )

    result = CliRunner().invoke(
        cli, ["-C", str(root), "log", "-n", "1", "--format", "yaml", "--show-files"]
    )
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["branch"] == "master"
    assert len(payload["entries"]) == 1
    entry = payload["entries"][0]
    assert entry["branch"] == "master"
    assert entry["operation"] == "concept.add"
    assert entry["message"] == "Add concept: log_yaml (testing:log_yaml)"
    assert "concepts/log_yaml.yaml" in entry["added"]
    assert entry["parents"]


def test_log_missing_branch_errors(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    Repository.init(root)
    result = CliRunner().invoke(
        cli, ["-C", str(root), "log", "--branch", "agent/missing"]
    )
    assert result.exit_code != 0
    assert "Branch not found: agent/missing" in result.output


def test_log_merge_summary_output(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    git = repo.require_git()
    primary = git.primary_branch_name()
    git.create_branch("left", source_commit=git.head_sha())
    git.create_branch("right", source_commit=git.head_sha())
    author_obs_claim(repo, "claim_left", "left says so", branch="left")
    author_obs_claim(repo, "claim_right", "right says so", branch="right")
    merge_sha = create_merge_commit(repo, "left", "right", target_branch=primary)
    assert merge_sha

    text_result = CliRunner().invoke(cli, ["-C", str(repo.root), "log", "-n", "1"])
    assert text_result.exit_code == 0, text_result.output
    assert "merge.commit" in text_result.output
    assert "merge: left + right;" in text_result.output

    yaml_result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "log", "-n", "1", "--format", "yaml"]
    )
    assert yaml_result.exit_code == 0, yaml_result.output
    entry = yaml.safe_load(yaml_result.output)["entries"][0]
    assert entry["operation"] == "merge.commit"
    assert {entry["merge"]["branch_a"], entry["merge"]["branch_b"]} == {"left", "right"}
    assert entry["merge"]["argument_count"] >= 2


def test_diff_and_show_output(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add a")
    git.commit_files(
        {"concepts/a.yaml": b"v: 2\n", "concepts/b.yaml": b"v: 1\n"},
        "update files",
    )
    sha = git.head_sha()
    assert sha is not None

    diff_result = CliRunner().invoke(cli, ["-C", str(root), "diff"])
    assert diff_result.exit_code == 0, diff_result.output
    assert "Added: concepts/b.yaml" in diff_result.output
    assert "Modified: concepts/a.yaml" in diff_result.output

    show_result = CliRunner().invoke(cli, ["-C", str(root), "show", sha])
    assert show_result.exit_code == 0, show_result.output
    assert f"Commit: {sha[:8]}" in show_result.output
    assert "Message: update files" in show_result.output
    assert "A concepts/b.yaml" in show_result.output


def test_show_missing_commit_errors(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    Repository.init(root)
    result = CliRunner().invoke(cli, ["-C", str(root), "show", "deadbeef"])
    assert result.exit_code == 2
    assert "Commit not found: deadbeef" in result.output


def test_checkout_rebuilds_sidecar(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "concept:mass", name="mass")
    sha = repo.require_git().head_sha()
    assert sha is not None

    result = CliRunner().invoke(cli, ["-C", str(repo.root), "checkout", sha])
    assert result.exit_code == 0, result.output
    assert f"Sidecar built from commit {sha[:8]}." in result.output


def test_checkout_missing_commit_errors(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    Repository.init(root)
    result = CliRunner().invoke(cli, ["-C", str(root), "checkout", "deadbeef"])
    assert result.exit_code == 2
    assert "Commit not found: deadbeef" in result.output
