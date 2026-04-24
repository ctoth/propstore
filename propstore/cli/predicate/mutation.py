from __future__ import annotations

import click

from propstore.app.predicates import (
    PredicateAddRequest,
    PredicateRemoveRequest,
    PredicateWorkflowError,
    add_predicate,
    remove_predicate,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_success
from propstore.cli.predicate import predicate
from propstore.repository import Repository


@predicate.command("add")
@click.option(
    "--file",
    "file_name",
    required=True,
    help="File stem in predicates/ (e.g. ikeda_2014). Creates or appends.",
)
@click.option(
    "--id",
    "predicate_id",
    required=True,
    help="Predicate name (e.g. aspirin_user).",
)
@click.option(
    "--arity",
    required=True,
    type=int,
    help="Non-negative integer number of argument positions.",
)
@click.option(
    "--arg-type",
    "arg_type",
    multiple=True,
    help="Per-position sort. Repeat to give one type per position; length must equal arity.",
)
@click.option(
    "--derived-from",
    "derived_from",
    default=None,
    help="Optional derived_from DSL describing how propstore data materialises this predicate.",
)
@click.option(
    "--description",
    default=None,
    help="Optional human-readable explanation.",
)
@click.pass_obj
def add(
    obj: dict,
    file_name: str,
    predicate_id: str,
    arity: int,
    arg_type: tuple[str, ...],
    derived_from: str | None,
    description: str | None,
) -> None:
    """Add a predicate declaration to predicates/<file>.yaml.

    Creates the file if it does not exist, or appends an entry
    otherwise. Duplicate predicate ids inside a single file are
    rejected.
    """
    repo: Repository = obj["repo"]
    request = PredicateAddRequest(
        file=file_name,
        predicate_id=predicate_id,
        arity=arity,
        arg_types=tuple(arg_type),
        derived_from=derived_from,
        description=description,
    )
    try:
        report = add_predicate(repo, request)
    except PredicateWorkflowError as exc:
        fail(exc)

    if report.created:
        emit_success(f"Created {report.filepath}")
    else:
        emit_success(f"Updated {report.filepath}")
    emit(f"  + predicate {predicate_id}/{arity}")


@predicate.command("remove")
@click.option(
    "--file",
    "file_name",
    required=True,
    help="File stem in predicates/ (e.g. ikeda_2014).",
)
@click.option(
    "--id",
    "predicate_id",
    required=True,
    help="Predicate name to remove (e.g. aspirin_user).",
)
@click.pass_obj
def remove(obj: dict, file_name: str, predicate_id: str) -> None:
    """Remove a predicate from predicates/<file>.yaml.

    Rejects if the file does not exist or the predicate id is absent.
    """
    repo: Repository = obj["repo"]
    request = PredicateRemoveRequest(file=file_name, predicate_id=predicate_id)
    try:
        report = remove_predicate(repo, request)
    except PredicateWorkflowError as exc:
        fail(exc)

    emit_success(f"Removed predicate '{report.predicate_id}' from {report.filepath}")
