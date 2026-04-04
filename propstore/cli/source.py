"""pks source - source lifecycle commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.repository import Repository
from propstore.source_ops import (
    commit_source_metadata,
    commit_source_notes,
    init_source_branch,
    source_branch_name,
)


@click.group()
def source() -> None:
    """Manage source branches and source-local artifacts."""


@source.command("init")
@click.argument("name")
@click.option("--kind", "kind_name", required=True)
@click.option("--origin-type", required=True)
@click.option("--origin-value", required=True)
@click.pass_obj
def source_init(
    obj: dict,
    name: str,
    kind_name: str,
    origin_type: str,
    origin_value: str,
) -> None:
    repo: Repository = obj["repo"]
    branch = init_source_branch(
        repo,
        name,
        kind=kind_name,
        origin_type=origin_type,
        origin_value=origin_value,
    )
    click.echo(f"Initialized {branch}")


@source.command("write-notes")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_notes(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    commit_source_notes(repo, name, file_path)
    click.echo(f"Wrote notes to {source_branch_name(name)}")


@source.command("write-metadata")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_metadata(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    commit_source_metadata(repo, name, file_path)
    click.echo(f"Wrote metadata to {source_branch_name(name)}")
