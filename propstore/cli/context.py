"""pks context — subcommands for managing contexts."""
from __future__ import annotations

import sys

import click

from propstore.artifacts import CONTEXT_FAMILY, ContextRef
from propstore.artifacts.codecs import encode_document
from propstore.artifacts.documents.contexts import ContextDocument
from propstore.cli.helpers import EXIT_ERROR
from propstore.repository import Repository
from propstore.artifacts.schema import convert_document_value
from propstore.validate_contexts import load_contexts


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
    contexts_dir = repo.contexts_dir
    contexts_tree = repo.tree() / "contexts"

    filepath = contexts_dir / f"{name}.yaml"
    if (contexts_tree / f"{name}.yaml").exists():
        click.echo(f"ERROR: Context file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    parameters: dict[str, str] = {}
    for raw_parameter in parameter:
        key, sep, value = raw_parameter.partition("=")
        if not sep or not key or not value:
            click.echo(
                f"ERROR: Context parameter '{raw_parameter}' must be KEY=VALUE",
                err=True,
            )
            sys.exit(EXIT_ERROR)
        parameters[key] = value

    data: dict = {
        "id": name,
        "name": name,
        "description": description,
    }
    structure: dict[str, object] = {}
    if assumption:
        structure["assumptions"] = list(assumption)
    if parameters:
        structure["parameters"] = parameters
    if perspective:
        structure["perspective"] = perspective
    if structure:
        data["structure"] = structure

    if dry_run:
        click.echo(f"Would create {filepath}")
        document = convert_document_value(
            data,
            ContextDocument,
            source=f"dry-run:contexts/{name}.yaml",
        )
        click.echo(encode_document(document).decode("utf-8"))
        return

    document = convert_document_value(
        data,
        ContextDocument,
        source=f"contexts/{name}.yaml",
    )
    repo.artifacts.save(
        CONTEXT_FAMILY,
        ContextRef(name),
        document,
        message=f"Add context: {name}",
    )
    repo.snapshot.sync_worktree()

    click.echo(f"Created {filepath}")


@context.command("list")
@click.pass_obj
def list_contexts(obj: dict) -> None:
    """List all registered contexts."""
    repo: Repository = obj["repo"]
    contexts = load_contexts(repo.tree() / "contexts")
    if not contexts:
        click.echo("No contexts registered.")
        return

    for context in contexts:
        record = context.record
        cid = context.filename if record.context_id is None else str(record.context_id)
        desc = record.description or ""
        suffix = f" ({record.perspective})" if record.perspective else ""
        click.echo(f"  {cid}{suffix} — {desc}")
