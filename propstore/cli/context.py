"""pks context — subcommands for managing contexts."""
from __future__ import annotations

import sys

import click

from propstore.cli.output import emit

from quire.documents import encode_document
from propstore.cli.helpers import EXIT_ERROR
from propstore.app.contexts import (
    ContextAddRequest,
    ContextWorkflowError,
    add_context,
    list_context_items,
)
from propstore.repository import Repository


@click.group()
def context() -> None:
    """Manage contexts in the registry."""


@context.command()
@click.option("--name", required=True, help="Context ID (e.g., ctx_atms_tradition)")
@click.option("--description", required=True, help="Short description")
@click.option("--assumption", multiple=True, help="Context-local CEL assumption")
@click.option("--parameter", multiple=True, help="Context parameter as KEY=VALUE")
@click.option("--perspective", default=None, help="Named perspective for this context")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    name: str,
    description: str,
    assumption: tuple[str, ...],
    parameter: tuple[str, ...],
    perspective: str | None,
    dry_run: bool,
) -> None:
    """Add a new context to the registry."""
    repo: Repository = obj["repo"]
    request = ContextAddRequest(
        name=name,
        description=description,
        assumptions=assumption,
        parameters=parameter,
        perspective=perspective,
    )
    try:
        report = add_context(repo, request, dry_run=dry_run)
    except ContextWorkflowError as exc:
        emit(f"ERROR: {exc}", err=True)
        sys.exit(EXIT_ERROR)

    if not report.created:
        emit(f"Would create {report.filepath}")
        emit(encode_document(report.document).decode("utf-8"))
        return

    emit(f"Created {report.filepath}")


@context.command("list")
@click.pass_obj
def list_contexts(obj: dict) -> None:
    """List all registered contexts."""
    repo: Repository = obj["repo"]
    contexts = list_context_items(repo)
    if not contexts:
        emit("No contexts registered.")
        return

    for context in contexts:
        suffix = f" ({context.perspective})" if context.perspective else ""
        emit(f"  {context.context_id}{suffix} — {context.description}")
