from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.app.contexts import (
    ContextAddRequest,
    ContextNotFoundError,
    ContextReferencedError,
    ContextSearchRequest,
    ContextWorkflowError,
    add_context,
    list_context_items,
    remove_context,
    search_context_items,
    show_context,
)
from propstore.cli import cli
from propstore.families.documents.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.families.documents.worldlines import (
    WorldlineDefinitionDocument,
    WorldlineInputsDocument,
)
from propstore.families.registry import SourceRef, WorldlineRef
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


def test_context_show_and_search_owner_reports(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(
            name="ctx_real",
            description="Real context",
            perspective="analyst",
        ),
        dry_run=False,
    )

    shown = show_context(repo, "ctx_real")
    searched = search_context_items(
        repo,
        ContextSearchRequest(query="analyst", limit=10),
    )

    assert shown.filepath == repo.contexts_dir / "ctx_real.yaml"
    assert "description: Real context" in shown.rendered
    assert [item.context_id for item in searched] == ["ctx_real"]

    try:
        show_context(repo, "missing")
    except ContextNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing context failure")


def test_context_cli_show_and_search_use_owner_reports(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(
            name="ctx_real",
            description="Real context",
            perspective="analyst",
        ),
        dry_run=False,
    )
    runner = CliRunner()

    shown = runner.invoke(cli, ["-C", str(repo.root), "context", "show", "ctx_real"])
    searched = runner.invoke(cli, ["-C", str(repo.root), "context", "search", "analyst"])

    assert shown.exit_code == 0, shown.output
    assert "description: Real context" in shown.output
    assert searched.exit_code == 0, searched.output
    assert "ctx_real (analyst) — Real context" in searched.output


def test_remove_context_blocks_referenced_artifacts_and_supports_force(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(
            name="ctx_real",
            description="Real context",
        ),
        dry_run=False,
    )
    repo.families.source_claims.save(
        SourceRef("paper"),
        SourceClaimsDocument(
            claims=(SourceClaimDocument(id="claim-a", context="ctx_real"),),
        ),
        message="Add source claims",
    )
    repo.families.worldlines.save(
        WorldlineRef("demo"),
        WorldlineDefinitionDocument(
            id="demo",
            targets=("target",),
            inputs=WorldlineInputsDocument(context_id="ctx_real"),
        ),
        message="Add worldline",
    )

    try:
        remove_context(repo, "ctx_real", force=False, dry_run=False)
    except ContextReferencedError as exc:
        assert exc.references == (
            "source-claim:paper:claim-a",
            "worldline:demo",
        )
    else:
        raise AssertionError("expected referenced context failure")

    dry_run = remove_context(repo, "ctx_real", force=True, dry_run=True)
    forced = remove_context(repo, "ctx_real", force=True, dry_run=False)

    assert dry_run.removed is False
    assert dry_run.references == (
        "source-claim:paper:claim-a",
        "worldline:demo",
    )
    assert forced.removed is True
    assert not (repo.contexts_dir / "ctx_real.yaml").exists()


def test_context_cli_remove_uses_owner_reference_checks(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(
            name="ctx_real",
            description="Real context",
        ),
        dry_run=False,
    )
    repo.families.source_claims.save(
        SourceRef("paper"),
        SourceClaimsDocument(
            claims=(SourceClaimDocument(id="claim-a", context="ctx_real"),),
        ),
        message="Add source claims",
    )
    runner = CliRunner()

    blocked = runner.invoke(cli, ["-C", str(repo.root), "context", "remove", "ctx_real"])
    dry_run = runner.invoke(
        cli,
        ["-C", str(repo.root), "context", "remove", "ctx_real", "--force", "--dry-run"],
    )
    forced = runner.invoke(
        cli,
        ["-C", str(repo.root), "context", "remove", "ctx_real", "--force"],
    )

    assert blocked.exit_code != 0, blocked.output
    assert "source-claim:paper:claim-a" in blocked.output
    assert "Use --force to remove anyway." in blocked.output
    assert dry_run.exit_code == 0, dry_run.output
    assert "Would remove" in dry_run.output
    assert forced.exit_code == 0, forced.output
    assert "Removed" in forced.output
