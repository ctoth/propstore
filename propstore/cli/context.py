"""pks context — subcommands for managing contexts."""
from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

from propstore.cli.helpers import EXIT_ERROR
from propstore.cli.repository import Repository
from propstore.validate_contexts import load_contexts


@click.group()
def context() -> None:
    """Manage contexts in the registry."""


@context.command()
@click.option("--name", required=True, help="Context ID (e.g., ctx_atms_tradition)")
@click.option("--description", required=True, help="Short description")
@click.option("--inherits", default=None, help="Parent context ID")
@click.option("--excludes", default=None, help="Comma-separated excluded context IDs")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    name: str,
    description: str,
    inherits: str | None,
    excludes: str | None,
    dry_run: bool,
) -> None:
    """Add a new context to the registry."""
    repo: Repository = obj["repo"]
    git = repo.git
    if git is None:
        raise click.ClickException("context mutations require a git-backed repository")
    contexts_dir = repo.contexts_dir
    contexts_tree = repo.tree() / "contexts"

    filepath = contexts_dir / f"{name}.yaml"
    if (contexts_tree / f"{name}.yaml").exists():
        click.echo(f"ERROR: Context file '{filepath}' already exists", err=True)
        sys.exit(EXIT_ERROR)

    # Validate inherits reference
    if inherits:
        parent_path = contexts_tree / f"{inherits}.yaml"
        if not parent_path.exists():
            click.echo(f"ERROR: Parent context '{inherits}' does not exist", err=True)
            sys.exit(EXIT_ERROR)

    data: dict = {
        "id": name,
        "name": name,
        "description": description,
    }
    if inherits:
        data["inherits"] = inherits
    if excludes:
        data["excludes"] = [e.strip() for e in excludes.split(",")]

    if dry_run:
        click.echo(f"Would create {filepath}")
        click.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    yaml_bytes = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    rel_path = filepath.relative_to(repo.root).as_posix()
    git.commit_files({rel_path: yaml_bytes}, f"Add context: {name}")
    git.sync_worktree()

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
        inherits = None if record.inherits is None else str(record.inherits)
        suffix = f" (inherits {inherits})" if inherits else ""
        click.echo(f"  {cid}{suffix} — {desc}")
