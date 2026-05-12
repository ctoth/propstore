from __future__ import annotations

import click

from propstore.app.rules import (
    RuleNotFoundError,
    list_rules,
    show_rule,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_table
from propstore.cli.rule import rule
from propstore.repository import Repository


@rule.command("list")
@click.pass_obj
def list_cmd(obj: dict) -> None:
    """List authored rule artifacts."""
    repo: Repository = obj["repo"]
    items = list_rules(repo)
    if not items:
        emit("No rules.")
        return
    emit_table(
        ("GROUP", "RULE", "KIND", "PAPER"),
        [
            (item.authoring_group or "", item.rule_id, item.kind, item.paper or "")
            for item in items
        ],
    )


@rule.command("show")
@click.argument("rule_id")
@click.pass_obj
def show(obj: dict, rule_id: str) -> None:
    """Show one rule artifact."""
    repo: Repository = obj["repo"]
    try:
        report = show_rule(repo, rule_id)
    except RuleNotFoundError:
        fail(f"Rule '{rule_id}' not found")
    emit(report.rendered)
