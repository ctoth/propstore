"""``pks predicate list`` / ``show`` — read projections over the predicate family.

Thin read adapters: they iterate / load the stored
:class:`~propstore.families.predicates.Predicate` documents and render them; no
read view or filtering logic lives here (CLAUDE.md "CLI adapter discipline").
"""
from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table
from propstore.cli.predicate import predicate
from propstore.families.predicates import Predicate


@predicate.command("list")
@click.pass_obj
def predicate_list(obj: CliContext) -> None:
    """List every declared predicate."""

    repo = require_repo(obj)
    predicates = sorted(
        (handle.document for handle in repo.families.predicate.iter_handles()),
        key=lambda item: item.predicate_id,
    )
    if not predicates:
        emit("No predicates declared.")
        return
    emit_table(
        ("GROUP", "PREDICATE", "ARITY", "ARG TYPES"),
        [
            (
                item.authoring_group or "",
                item.predicate_id,
                item.arity,
                ", ".join(item.arg_types),
            )
            for item in predicates
        ],
    )


@predicate.command("show")
@click.argument("predicate_id")
@click.pass_obj
def predicate_show(obj: CliContext, predicate_id: str) -> None:
    """Show one predicate's rendered YAML document."""

    repo = require_repo(obj)
    loaded = repo.families.predicate.load(predicate_id)
    if not isinstance(loaded, Predicate):
        fail(f"Predicate '{predicate_id}' not found")
    emit(repo.families.predicate.render(loaded))
