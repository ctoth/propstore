from __future__ import annotations

import shutil
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
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import make_test_context_commit_entry, normalize_claims_payload, normalize_concept_payloads


def _concept_payload(
    local_id: str,
    canonical_name: str,
    *,
    domain: str,
    form: str,
    **extra: object,
) -> dict:
    payload = {
        "id": local_id,
        "canonical_name": canonical_name,
        "status": "proposed",
        "definition": f"{canonical_name} definition",
        "domain": domain,
        "form": form,
    }
    payload.update(extra)
    return normalize_concept_payloads([payload])[0]


def test_log_output(tmp_path: Path) -> None:
    """pks log shows history after operations."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)

    package_forms = Path(__file__).resolve().parent.parent / "propstore" / "_resources" / "forms"
    for form_file in package_forms.glob("*.yaml"):
        shutil.copy2(form_file, repo.forms_dir / form_file.name)

    git = repo.git
    assert git is not None
    form_files = {
        form.relative_to(repo.root).as_posix(): form.read_bytes()
        for form in sorted(repo.forms_dir.glob("*.yaml"))
    }
    git.commit_files(form_files, "Seed forms")
    git.sync_worktree()

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
    result = runner.invoke(cli, ["-C", str(root), "log", "--branch", "agent/demo", "-n", "1"])
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


def test_log_yaml_output(tmp_path: Path) -> None:
    """pks log --format yaml returns structured branch-aware records."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None

    git.commit_files(
        {"concepts/log_yaml.yaml": b"canonical_name: log_yaml\n"},
        "Add concept: log_yaml (testing:log_yaml)",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "log", "-n", "1", "--format", "yaml", "--show-files"])
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


def test_log_report_builds_structured_records(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None

    git.commit_files(
        {"concepts/log_report.yaml": b"canonical_name: log_report\n"},
        "Add concept: log_report (testing:log_report)",
    )

    report = build_log_report(
        repo,
        count=1,
        branch_name=None,
        show_files=True,
    )
    payload = report.to_payload(show_files=True)

    assert report.branch == "master"
    assert len(report.entries) == 1
    assert report.entries[0].operation == "concept.add"
    assert payload["entries"][0]["added"] == ["concepts/log_report.yaml"]


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


def test_log_merge_summary_output(tmp_path: Path) -> None:
    """pks log reports merge manifest summaries for storage merge commits."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None

    base_sha = git.commit_files({"concepts/base.yaml": b"canonical_name: base\n"}, "seed")
    git.create_branch("agent/demo", source_commit=base_sha)
    git.commit_files(
        {"concepts/agent_demo.yaml": b"canonical_name: agent_demo\n"},
        "branch update",
        branch="agent/demo",
    )

    merge_sha = create_merge_commit(repo.snapshot, "master", "agent/demo")
    assert merge_sha

    runner = CliRunner()
    text_result = runner.invoke(cli, ["-C", str(root), "log", "-n", "1"])
    assert text_result.exit_code == 0, text_result.output
    assert "merge.commit" in text_result.output
    assert "merge: master + agent/demo;" in text_result.output
    assert "semantic_candidates=0" in text_result.output

    yaml_result = runner.invoke(cli, ["-C", str(root), "log", "-n", "1", "--format", "yaml"])
    assert yaml_result.exit_code == 0, yaml_result.output
    payload = yaml.safe_load(yaml_result.output)
    entry = payload["entries"][0]
    assert entry["operation"] == "merge.commit"
    assert entry["merge"]["branch_a"] == "master"
    assert entry["merge"]["branch_b"] == "agent/demo"
    assert entry["merge"]["semantic_candidate_count"] == 0
    assert entry["merge"]["materialized_argument_count"] == 0


def test_log_missing_branch_errors(tmp_path: Path) -> None:
    """pks log --branch rejects unknown branch names."""
    root = tmp_path / "knowledge"
    Repository.init(root)

    runner = CliRunner()
    result = runner.invoke(cli, ["-C", str(root), "log", "--branch", "agent/missing"])
    assert result.exit_code != 0
    assert "Branch not found: agent/missing" in result.output


@pytest.mark.e2e
def test_log_yaml_reports_worldline_materialization_history(tmp_path: Path) -> None:
    """A real build/create/run flow should surface stable operations in git history."""
    root = tmp_path / "knowledge"
    repo = Repository.init(root)
    git = repo.git
    assert git is not None
    context_path, context_body = make_test_context_commit_entry()

    concept = _concept_payload(
        "concept1",
        "log_temperature",
        domain="testing",
        form="scalar",
        status="accepted",
        definition="A temperature used for end-to-end history coverage.",
    )
    claims_doc = normalize_claims_payload(
        {
            "source": {"paper": "log-demo"},
            "claims": [
                {
                    "id": "temp_claim",
                    "type": "parameter",
                    "concept": concept["artifact_id"],
                    "value": 42.0,
                    "unit": "celsius",
                    "provenance": {"paper": "log-demo", "page": 1},
                }
            ],
        }
    )
    git.commit_files(
        {
            "forms/scalar.yaml": yaml.safe_dump(
                {"name": "scalar", "dimensionless": True},
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8"),
            "concepts/log_temperature.yaml": yaml.safe_dump(
                concept,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8"),
            "claims/log_temperature.yaml": yaml.safe_dump(
                claims_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8"),
            context_path: context_body,
        },
        "Seed worldline inputs",
    )
    git.sync_worktree()

    runner = CliRunner()
    build_result = runner.invoke(cli, ["-C", str(root), "build", "--force"])
    assert build_result.exit_code == 0, build_result.output

    create_result = runner.invoke(
        cli,
        [
            "-C",
            str(root),
            "worldline",
            "create",
            "log_worldline",
            "--target",
            "log_temperature",
        ],
    )
    assert create_result.exit_code == 0, create_result.output

    rebuild_result = runner.invoke(cli, ["-C", str(root), "build", "--force"])
    assert rebuild_result.exit_code == 0, rebuild_result.output

    run_result = runner.invoke(
        cli,
        ["-C", str(root), "worldline", "run", "log_worldline"],
    )
    assert run_result.exit_code == 0, run_result.output

    result = runner.invoke(
        cli,
        ["-C", str(root), "log", "-n", "2", "--format", "yaml"],
    )
    assert result.exit_code == 0, result.output
    payload = yaml.safe_load(result.output)
    assert payload["branch"] == "master"
    assert [entry["operation"] for entry in payload["entries"]] == [
        "worldline.materialize",
        "worldline.create",
    ]
    assert all(entry["branch"] == "master" for entry in payload["entries"])
