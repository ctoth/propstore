"""pks context — subcommands for managing contexts."""
from __future__ import annotations

import click

from propstore.cli.output import emit, emit_success

from quire.documents import encode_document
from propstore.cli.helpers import fail
from propstore.app.contexts import (
    ContextAddRequest,
    ContextNotFoundError,
    ContextSearchRequest,
    ContextWorkflowError,
    add_context,
    list_context_items,
    search_context_items,
    show_context,
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
        fail(exc)

    if not report.created:
        emit(f"Would create {report.filepath}")
        emit(encode_document(report.document).decode("utf-8"))
        return

    emit_success(f"Created {report.filepath}")


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


@context.command("show")
@click.argument("name")
@click.pass_obj
def show(obj: dict, name: str) -> None:
    """Show one context YAML document."""
    repo: Repository = obj["repo"]
    try:
        report = show_context(repo, name)
    except ContextNotFoundError:
        fail(f"Context '{name}' not found")
    emit(report.rendered)


@context.command("search")
@click.argument("query")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows to show.")
@click.pass_obj
def search(obj: dict, query: str, limit: int) -> None:
    """Search contexts by id, description, or perspective."""
    repo: Repository = obj["repo"]
    items = search_context_items(
        repo,
        ContextSearchRequest(query=query, limit=limit),
    )
    if not items:
        emit("No matches.")
        return
    for item in items:
        suffix = f" ({item.perspective})" if item.perspective else ""
        emit(f"  {item.context_id}{suffix} — {item.description}")
