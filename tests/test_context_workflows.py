from __future__ import annotations

import yaml
from click.testing import CliRunner

from propstore.app.contexts import (
    ContextAddRequest,
    ContextLiftingRuleAddRequest,
    ContextLiftingRuleUpdateRequest,
    ContextNotFoundError,
    ContextReferencedError,
    ContextSearchRequest,
    ContextWorkflowError,
    add_context,
    add_context_lifting_rule,
    list_context_items,
    list_context_lifting_rules,
    remove_context,
    remove_context_lifting_rule,
    search_context_items,
    show_context_lifting_rule,
    show_context,
    update_context_lifting_rule,
)
from propstore.app.forms import FormAddRequest, add_form
from propstore.cli import cli
from propstore.families.documents.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.families.documents.worldlines import (
    WorldlineDefinitionDocument,
    WorldlineInputsDocument,
)
from propstore.families.registry import ContextRef, SourceRef, WorldlineRef
from propstore.repository import Repository


def _read_context_file(repo: Repository, name: str) -> dict:
    return yaml.safe_load(repo.git.read_file(f"contexts/{name}.yaml"))


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

    expected_path = repo.root / repo.families.contexts.address(ContextRef("ctx_test")).require_path()
    assert report.created is True
    assert report.filepath == expected_path
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
    dry_path = repo.root / repo.families.contexts.address(ContextRef("ctx_dry")).require_path()
    assert not dry_path.exists()
    assert add.exit_code == 0, add.output
    data = _read_context_file(repo, "ctx_real")
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

    expected_path = repo.root / repo.families.contexts.address(ContextRef("ctx_real")).require_path()
    assert shown.filepath == expected_path
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
    assert repo.families.contexts.load(ContextRef("ctx_real")) is None


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


def test_context_lifting_rule_workflows_crud(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(name="ctx_source", description="Source context"),
        dry_run=False,
    )
    add_context(
        repo,
        ContextAddRequest(name="ctx_target", description="Target context"),
        dry_run=False,
    )

    dry_run = add_context_lifting_rule(
        repo,
        "ctx_target",
        ContextLiftingRuleAddRequest(
            rule_id="lift_source_target",
            source_context="ctx_source",
            conditions=("license == 'bridge'",),
            justification="Bridge rule",
        ),
        dry_run=True,
    )
    created = add_context_lifting_rule(
        repo,
        "ctx_target",
        ContextLiftingRuleAddRequest(
            rule_id="lift_source_target",
            source_context="ctx_source",
            conditions=("license == 'bridge'",),
            justification="Bridge rule",
        ),
        dry_run=False,
    )
    items = list_context_lifting_rules(repo, "ctx_target")
    shown = show_context_lifting_rule(repo, "ctx_target", "lift_source_target")
    updated = update_context_lifting_rule(
        repo,
        "ctx_target",
        "lift_source_target",
        ContextLiftingRuleUpdateRequest(
            conditions=(),
            justification="Retargeted bridge",
        ),
        dry_run=False,
    )
    removed_dry_run = remove_context_lifting_rule(
        repo,
        "ctx_target",
        "lift_source_target",
        dry_run=True,
    )
    rewritten = _read_context_file(repo, "ctx_target")
    removed = remove_context_lifting_rule(
        repo,
        "ctx_target",
        "lift_source_target",
        dry_run=False,
    )

    assert dry_run.created is False
    assert created.created is True
    assert items[0].owner_context == "ctx_target"
    assert items[0].source_context == "ctx_source"
    assert items[0].target_context == "ctx_target"
    assert items[0].condition_count == 1
    assert "id: lift_source_target" in shown.rendered
    assert "source: ctx_source" in shown.rendered
    assert updated.updated is True
    assert "conditions" not in rewritten["lifting_rules"][0]
    assert rewritten["lifting_rules"][0]["justification"] == "Retargeted bridge"
    assert removed_dry_run.removed is False
    assert removed.removed is True
    assert _read_context_file(repo, "ctx_target").get("lifting_rules") is None


def test_context_lifting_rule_workflows_validate_source_and_cel(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(name="ctx_target", description="Target context"),
        dry_run=False,
    )

    try:
        add_context_lifting_rule(
            repo,
            "ctx_target",
            ContextLiftingRuleAddRequest(
                rule_id="lift_missing",
                source_context="ctx_missing",
            ),
            dry_run=False,
        )
    except ContextNotFoundError as exc:
        assert exc.name == "ctx_missing"
    else:
        raise AssertionError("expected missing source context failure")

    add_form(
        repo,
        FormAddRequest(
            name="boolean",
            dimensionless="true",
        ),
        dry_run=False,
    )
    runner = CliRunner()
    concept_add = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "concept",
            "add",
            "--domain",
            "speech",
            "--name",
            "pitch",
            "--definition",
            "Pitch",
            "--form",
            "boolean",
        ],
    )

    assert concept_add.exit_code == 0, concept_add.output

    try:
        add_context_lifting_rule(
            repo,
            "ctx_target",
            ContextLiftingRuleAddRequest(
                rule_id="lift_invalid",
                source_context="ctx_target",
                conditions=("(",),
            ),
            dry_run=False,
        )
    except ContextWorkflowError as exc:
        assert "lifting rule 'lift_invalid'" in str(exc)
        assert "condition[0]" in str(exc)
    else:
        raise AssertionError("expected invalid lifting-rule condition failure")


def test_context_lifting_cli_crud(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(name="ctx_source", description="Source context"),
        dry_run=False,
    )
    add_context(
        repo,
        ContextAddRequest(name="ctx_target", description="Target context"),
        dry_run=False,
    )
    runner = CliRunner()

    add = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "add",
            "ctx_target",
            "--rule-id",
            "lift_source_target",
            "--source",
            "ctx_source",
            "--condition",
            "license == 'bridge'",
            "--justification",
            "Bridge rule",
        ],
    )
    listed = runner.invoke(
        cli,
        ["-C", str(repo.root), "context", "lifting", "list", "ctx_target"],
    )
    shown = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "show",
            "ctx_target",
            "lift_source_target",
        ],
    )
    updated = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "update",
            "ctx_target",
            "lift_source_target",
            "--clear-conditions",
            "--clear-justification",
        ],
    )
    removed_dry_run = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "remove",
            "ctx_target",
            "lift_source_target",
            "--dry-run",
        ],
    )
    removed = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "remove",
            "ctx_target",
            "lift_source_target",
        ],
    )

    assert add.exit_code == 0, add.output
    assert "Added lifting rule 'lift_source_target'" in add.output
    assert listed.exit_code == 0, listed.output
    assert "ctx_target: lift_source_target [ctx_source -> ctx_target, mode=bridge, conditions=1]" in listed.output
    assert shown.exit_code == 0, shown.output
    assert "justification: Bridge rule" in shown.output
    assert updated.exit_code == 0, updated.output
    assert "Updated lifting rule 'lift_source_target'" in updated.output
    assert removed_dry_run.exit_code == 0, removed_dry_run.output
    assert "Would remove lifting rule 'lift_source_target'" in removed_dry_run.output
    assert removed.exit_code == 0, removed.output
    assert "Removed lifting rule 'lift_source_target'" in removed.output


def test_context_lifting_cli_rejects_invalid_update_flags(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_context(
        repo,
        ContextAddRequest(name="ctx_target", description="Target context"),
        dry_run=False,
    )
    runner = CliRunner()

    conflict = runner.invoke(
        cli,
        [
            "-C",
            str(repo.root),
            "context",
            "lifting",
            "update",
            "ctx_target",
            "lift_missing",
            "--condition",
            "a == b",
            "--clear-conditions",
        ],
    )

    assert conflict.exit_code != 0, conflict.output
    assert "Cannot use --condition and --clear-conditions together" in conflict.output
