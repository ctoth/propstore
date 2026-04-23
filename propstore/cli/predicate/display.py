from __future__ import annotations

import click

from propstore.app.predicates import (
    PredicateFileNotFoundError,
    list_predicates,
    show_predicate_file,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_table
from propstore.cli.predicate import predicate
from propstore.repository import Repository


@predicate.command("list")
@click.pass_obj
def list_cmd(obj: dict) -> None:
    """List declared predicates across predicate files."""
    repo: Repository = obj["repo"]
    items = list_predicates(repo)
    if not items:
        emit("No predicates.")
        return
    emit_table(
        ("FILE", "PREDICATE", "ARITY", "ARG TYPES"),
        [
            (
                item.file,
                item.predicate_id,
                item.arity,
                ", ".join(item.arg_types),
            )
            for item in items
        ],
    )


@predicate.command("show")
@click.argument("file")
@click.pass_obj
def show(obj: dict, file: str) -> None:
    """Show one predicates/<file>.yaml document."""
    repo: Repository = obj["repo"]
    try:
        report = show_predicate_file(repo, file)
    except PredicateFileNotFoundError:
        fail(f"Predicate file '{file}' not found")
    emit(report.rendered)
