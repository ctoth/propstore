"""``pks rule list`` / ``show`` — read projections over the DeLP rule families.

Thin read adapters: they iterate / load the stored
:class:`~propstore.families.rules.DefeasibleRule` and
:class:`~propstore.families.rules.RuleSuperiority` documents and render them; no
read view or filtering logic lives here (CLAUDE.md "CLI adapter discipline").
"""

from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table
from propstore.cli.rule import rule
from propstore.families.rules import DefeasibleRule, RuleSuperiority


@rule.command("list")
@click.pass_obj
def rule_list(obj: CliContext) -> None:
    """List every authored rule and rule superiority."""

    repo = require_repo(obj)
    rules = sorted(
        (handle.document for handle in repo.families.defeasible_rule.iter_handles()),
        key=lambda item: item.rule_id,
    )
    superiorities = sorted(
        (handle.document for handle in repo.families.rule_superiority.iter_handles()),
        key=lambda item: item.superiority_id,
    )
    if not rules and not superiorities:
        emit("No rules authored.")
        return
    if rules:
        emit_table(
            ("GROUP", "RULE", "KIND", "HEAD", "SOURCE"),
            [
                (
                    item.authoring_group or "",
                    item.rule_id,
                    item.kind,
                    item.head.predicate,
                    item.source or "",
                )
                for item in rules
            ],
        )
    if superiorities:
        emit_table(
            ("GROUP", "SUPERIOR", "INFERIOR", "ARTIFACT"),
            [
                (
                    item.authoring_group or "",
                    item.superior_rule_id,
                    item.inferior_rule_id,
                    item.superiority_id,
                )
                for item in superiorities
            ],
        )


@rule.command("show")
@click.argument("rule_id")
@click.pass_obj
def rule_show(obj: CliContext, rule_id: str) -> None:
    """Show one rule's rendered YAML document."""

    repo = require_repo(obj)
    loaded = repo.families.defeasible_rule.load(rule_id)
    if not isinstance(loaded, DefeasibleRule):
        loaded_superiority = repo.families.rule_superiority.load(rule_id)
        if isinstance(loaded_superiority, RuleSuperiority):
            emit(repo.families.rule_superiority.render(loaded_superiority))
            return
        fail(f"Rule '{rule_id}' not found")
    emit(repo.families.defeasible_rule.render(loaded))
