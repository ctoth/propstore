from __future__ import annotations

import click

from propstore.app.rules import (
    RuleFileNotFoundError,
    list_rules,
    show_rule_file,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_table
from propstore.cli.rule import rule
from propstore.repository import Repository


@rule.command("list")
@click.pass_obj
def list_cmd(obj: dict) -> None:
    """List authored rules across rule files."""
    repo: Repository = obj["repo"]
    items = list_rules(repo)
    if not items:
        emit("No rules.")
        return
    emit_table(
        ("FILE", "RULE", "KIND", "PAPER"),
        [(item.file, item.rule_id, item.kind, item.paper or "") for item in items],
    )


@rule.command("show")
@click.argument("file")
@click.pass_obj
def show(obj: dict, file: str) -> None:
    """Show one rules/<file>.yaml document."""
    repo: Repository = obj["repo"]
    try:
        report = show_rule_file(repo, file)
    except RuleFileNotFoundError:
        fail(f"Rule file '{file}' not found")
    emit(report.rendered)
