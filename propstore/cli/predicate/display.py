from __future__ import annotations

import click

from propstore.app.predicates import (
    PredicateNotFoundError,
    list_predicates,
    show_predicate,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_table
from propstore.cli.predicate import predicate
from propstore.repository import Repository


@predicate.command("list")
@click.pass_obj
def list_cmd(obj: dict) -> None:
    """List declared predicate artifacts."""
    repo: Repository = obj["repo"]
    items = list_predicates(repo)
    if not items:
        emit("No predicates.")
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
            for item in items
        ],
    )


@predicate.command("show")
@click.argument("predicate_id")
@click.pass_obj
def show(obj: dict, predicate_id: str) -> None:
    """Show one predicate artifact."""
    repo: Repository = obj["repo"]
    try:
        report = show_predicate(repo, predicate_id)
    except PredicateNotFoundError:
        fail(f"Predicate '{predicate_id}' not found")
    emit(report.rendered)
