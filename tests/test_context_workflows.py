from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.cli import cli
from propstore.context_workflows import (
    ContextAddRequest,
    ContextWorkflowError,
    add_context,
    list_context_items,
)
from propstore.repository import Repository


def test_add_context_workflow_writes_structured_document(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    report = add_context(
        repo,
        ContextAddRequest(
            name="ctx_test",
            description="A test context",
            assumptions=("framework == 'general'",),
            parameters=("domain=speech",),
            perspective="local-model",
        ),
        dry_run=False,
    )
    items = list_context_items(repo)

    assert report.created is True
    assert report.filepath == repo.contexts_dir / "ctx_test.yaml"
    assert report.document.structure.parameters == {"domain": "speech"}
    assert len(items) == 1
    assert items[0].context_id == "ctx_test"
    assert items[0].perspective == "local-model"


def test_add_context_workflow_validates_duplicate_and_parameter_shape(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    request = ContextAddRequest(
        name="ctx_test",
        description="A test context",
        parameters=("domain=speech",),
    )

    add_context(repo, request, dry_run=False)

    try:
        add_context(repo, request, dry_run=False)
    except ContextWorkflowError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("expected duplicate context failure")

    try:
        add_context(
            repo,
            ContextAddRequest(
                name="ctx_other",
                description="Other",
                parameters=("not-a-pair",),
            ),
            dry_run=True,
        )
    except ContextWorkflowError as exc:
        assert "must be KEY=VALUE" in str(exc)
    else:
        raise AssertionError("expected malformed parameter failure")


def test_context_cli_add_dry_run_and_list_use_owner_reports(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    runner = CliRunner()

    dry_run = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "add",
            "--name",
            "ctx_dry",
            "--description",
            "Dry run",
            "--parameter",
            "domain=speech",
            "--dry-run",
        ],
    )
    add = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "add",
            "--name",
            "ctx_real",
            "--description",
            "Real context",
            "--perspective",
            "analyst",
        ],
    )
    listed = runner.invoke(cli, ["-C", str(repo.root), "context", "list"])

    assert dry_run.exit_code == 0, dry_run.output
    assert "Would create" in dry_run.output
    assert not (repo.contexts_dir / "ctx_dry.yaml").exists()
    assert add.exit_code == 0, add.output
    data = yaml.safe_load((repo.contexts_dir / "ctx_real.yaml").read_text())
    assert data["id"] == "ctx_real"
    assert listed.exit_code == 0, listed.output
    assert "ctx_real (analyst) — Real context" in listed.output
