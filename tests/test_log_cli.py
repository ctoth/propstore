from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.app.repository_history import (
    BranchNotFoundError,
    build_log_report,
    classify_log_operation,
)
from propstore.repository import Repository
from propstore.merge.merge_commit import create_merge_commit
from tests.conftest import (
    make_test_context_commit_entry,
    normalize_claims_payload,
)


def test_log_output(tmp_path: Path) -> None:
    """pks log shows history after operations."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    package_forms = (
        Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    )

    git = repo.git
    assert git is not None
    form_files = {
        f"forms/{form.name}": form.read_bytes()
        for form in sorted(package_forms.glob("*.yaml"))
    }
    git.commit_files(form_files, "Seed forms")

    runner = CliRunner()
    runner.invoke(
        cli,
        [
            "-C",
            str(root),
            "concept",
            "add",
            "--domain",
            "testing",
            "--name",
            "log_test",
            "--definition",
            "Testing log",
            "--form",
            "boolean",
        ],
    )

    result = runner.invoke(cli, ["-C", str(root), "log"])
    assert result.exit_code == 0, result.output
    assert "[master]" in result.output
    assert "concept.add" in result.output
    assert "log_test" in result.output
    assert "Seed forms" in result.output


def test_log_branch_output(tmp_path: Path) -> None:
    """pks log --branch scopes history to the requested branch."""
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

    runner = CliRunner()
    result = runner.invoke(
        cli, ["-C", str(root), "log", "--branch", "agent/demo", "-n", "1"]
    )
    assert result.exit_code == 0, result.output
    assert "[agent/demo]" in result.output
    assert "concept.add" in result.output
    assert "agent_demo" in result.output


def test_log_show_files_output(tmp_path: Path) -> None:
    """pks log --show-files includes per-commit file changes."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None

    git.commit_files({"concepts/a.yaml": b"v: 1\n"}, "add a")
    git.commit_files(
        {
            "concepts/a.yaml": b"v: 2\n",
            "concepts/b.yaml": b"v: 1\n",
        },
        "update files",
    )
    git.commit_deletes(["concepts/a.yaml"], "delete a")

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "log", "-n", "2", "--show-files"])
    assert result.exit_code == 0, result.output
    assert "D concepts/a.yaml" in result.output
    assert "A concepts/b.yaml" in result.output
    assert "M concepts/a.yaml" in result.output


def test_log_report_rejects_missing_branch(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    try:
        build_log_report(
            repo,
            count=1,
            branch_name="agent/missing",
            show_files=False,
        )
    except BranchNotFoundError as exc:
        assert str(exc) == "Branch not found: agent/missing"
    else:
        raise AssertionError("expected missing branch failure")


def test_log_operation_classifier_identifies_merge_from_parents() -> None:
    assert classify_log_operation("ordinary message", ("a", "b")) == "merge.commit"
    assert classify_log_operation("Add form: score", ()) == "form.add"
    assert classify_log_operation("ordinary message", ()) == "commit"


def test_log_missing_branch_errors(tmp_path: Path) -> None:
    """pks log --branch rejects unknown branch names."""
    root = tmp_path / "knowledge"
    Repository.init(root)

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "log", "--branch", "agent/missing"])
    assert result.exit_code != 0
    assert "Branch not found: agent/missing" in result.output
