"""pks rule — subcommands for authoring DeLP rules."""

from __future__ import annotations

import click

from propstore.app.rules import RuleAddRequest, RuleWorkflowError, add_rule
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_success
from propstore.repository import Repository


@click.group()
def rule() -> None:
    """Author DeLP strict, defeasible, and defeater rules."""


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
    type=click.Choice(["strict", "defeasible", "defeater"], case_sensitive=False),
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
    help="Body atom in the same DSL form. Repeat for each body literal.",
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
