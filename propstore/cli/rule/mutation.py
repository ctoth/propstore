from __future__ import annotations

import click

from propstore.app.rules import (
    RuleAddRequest,
    RuleRemoveRequest,
    RuleWorkflowError,
    add_rule,
    remove_rule,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_success
from propstore.cli.rule import rule
from propstore.repository import Repository


@rule.command("add")
@click.option(
    "--file",
    "file_name",
    required=True,
    help="File stem in rules/ (e.g. ikeda_2014). Creates or appends.",
)
@click.option(
    "--paper",
    required=True,
    help="Source paper slug for the rules file (source.paper in YAML).",
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
    """Add a rule to rules/<file>.yaml.

    Creates the file if it does not exist (with source.paper set from
    --paper), or appends an entry otherwise. Appending requires the
    paper to match.
    """
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

    if report.created:
        emit_success(f"Created {report.filepath}")
    else:
        emit_success(f"Updated {report.filepath}")
    emit(f"  + {kind} rule {rule_id}")


@rule.command("remove")
@click.option(
    "--file",
    "file_name",
    required=True,
    help="File stem in rules/ (e.g. ikeda_2014).",
)
@click.option(
    "--id",
    "rule_id",
    required=True,
    help="Authoring id of the rule to remove.",
)
@click.pass_obj
def remove(obj: dict, file_name: str, rule_id: str) -> None:
    """Remove a rule from rules/<file>.yaml.

    Rejects if the file does not exist, if the rule id is absent, or
    if the rule still participates in a superiority pair (remove the
    pair first).
    """
    repo: Repository = obj["repo"]
    request = RuleRemoveRequest(file=file_name, rule_id=rule_id)
    try:
        report = remove_rule(repo, request)
    except RuleWorkflowError as exc:
        fail(exc)

    emit_success(f"Removed rule '{report.rule_id}' from {report.filepath}")
