from __future__ import annotations

import click

from propstore.app.rules import (
    RuleAddRequest,
    RuleRemoveRequest,
    RuleSuperiorityAddRequest,
    RuleSuperiorityRemoveRequest,
    RuleWorkflowError,
    add_rule,
    add_rule_superiority,
    list_rule_superiority,
    remove_rule,
    remove_rule_superiority,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_success, emit_table
from propstore.cli.rule import rule
from propstore.repository import Repository


@rule.command("add")
@click.option(
    "--file",
    "file_name",
    required=False,
    default=None,
    help="Optional authoring group metadata (e.g. ikeda_2014).",
)
@click.option(
    "--paper",
    required=True,
    help="Source paper slug for rule provenance (source.paper in YAML).",
)
@click.option(
    "--id",
    "rule_id",
    required=True,
    help="Authoring id for the rule (e.g. r_ikeda_mi).",
)
@click.option(
    "--kind",
    type=click.Choice(
        ["strict", "defeasible", "proper_defeater", "blocking_defeater"],
        case_sensitive=False,
    ),
    required=True,
    help="Rule kind.",
)
@click.option(
    "--head",
    required=True,
    help=(
        "Head atom in DSL form: [~]pred(arg1, arg2). Leading ~ is strong negation. "
        "Uppercase terms are variables; lowercase/quoted are constants."
    ),
)
@click.option(
    "--body",
    multiple=True,
    help="Body literal in the same DSL form; prefix with 'not ' for default negation.",
)
@click.pass_obj
def add(
    obj: dict,
    file_name: str,
    paper: str,
    rule_id: str,
    kind: str,
    head: str,
    body: tuple[str, ...],
) -> None:
    """Add a rule artifact."""
    repo: Repository = obj["repo"]
    request = RuleAddRequest(
        file=file_name,
        paper=paper,
        rule_id=rule_id,
        kind=kind.lower(),
        head=head,
        body=tuple(body),
    )
    try:
        report = add_rule(repo, request)
    except RuleWorkflowError as exc:
        fail(exc)

    emit_success(f"Created {report.filepath}")
    emit(f"  + {kind} rule {rule_id}")


@rule.command("remove")
@click.option(
    "--id",
    "rule_id",
    required=True,
    help="Authoring id of the rule to remove.",
)
@click.pass_obj
def remove(obj: dict, rule_id: str) -> None:
    """Remove a rule artifact."""
    repo: Repository = obj["repo"]
    request = RuleRemoveRequest(rule_id=rule_id)
    try:
        report = remove_rule(repo, request)
    except RuleWorkflowError as exc:
        fail(exc)

    emit_success(f"Removed rule '{report.rule_id}' from {report.filepath}")


@rule.group("superiority")
def superiority() -> None:
    """Manage authored rule-priority pairs."""


@superiority.command("add")
@click.option(
    "--file",
    "file_name",
    required=False,
    default=None,
    help="Optional authoring group metadata (e.g. ikeda_2014).",
)
@click.option(
    "--superior",
    "superior_rule_id",
    required=True,
    help="Rule id that has priority.",
)
@click.option(
    "--inferior",
    "inferior_rule_id",
    required=True,
    help="Rule id that yields to the superior rule.",
)
@click.pass_obj
def superiority_add(
    obj: dict,
    file_name: str,
    superior_rule_id: str,
    inferior_rule_id: str,
) -> None:
    """Add a rule-superiority artifact."""
    repo: Repository = obj["repo"]
    request = RuleSuperiorityAddRequest(
        file=file_name,
        superior_rule_id=superior_rule_id,
        inferior_rule_id=inferior_rule_id,
    )
    try:
        report = add_rule_superiority(repo, request)
    except RuleWorkflowError as exc:
        fail(exc)

    emit_success(
        f"Added superiority {report.superior_rule_id} > "
        f"{report.inferior_rule_id} at {report.filepath}"
    )


@superiority.command("list")
@click.pass_obj
def superiority_list(obj: dict) -> None:
    """List rule-superiority artifacts."""
    repo: Repository = obj["repo"]
    items = list_rule_superiority(repo)
    if not items:
        emit("No rule superiority artifacts.")
        return
    emit_table(
        ("GROUP", "SUPERIOR", "INFERIOR", "ARTIFACT"),
        [
            (
                item.authoring_group or "",
                item.superior_rule_id,
                item.inferior_rule_id,
                item.artifact_id,
            )
            for item in items
        ],
    )


@superiority.command("remove")
@click.option(
    "--file",
    "file_name",
    required=False,
    default=None,
    help="Ignored authoring metadata retained for command symmetry.",
)
@click.option(
    "--superior",
    "superior_rule_id",
    required=True,
    help="Rule id that has priority.",
)
@click.option(
    "--inferior",
    "inferior_rule_id",
    required=True,
    help="Rule id that yields to the superior rule.",
)
@click.pass_obj
def superiority_remove(
    obj: dict,
    file_name: str,
    superior_rule_id: str,
    inferior_rule_id: str,
) -> None:
    """Remove a rule-superiority artifact."""
    repo: Repository = obj["repo"]
    request = RuleSuperiorityRemoveRequest(
        file=file_name,
        superior_rule_id=superior_rule_id,
        inferior_rule_id=inferior_rule_id,
    )
    try:
        report = remove_rule_superiority(repo, request)
    except RuleWorkflowError as exc:
        fail(exc)

    emit_success(
        f"Removed superiority {report.superior_rule_id} > "
        f"{report.inferior_rule_id} from {report.filepath}"
    )
