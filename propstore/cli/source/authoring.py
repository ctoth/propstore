"""Source-branch side-file authoring: notes and metadata.

``notes.md`` and ``metadata.json`` are the two opaque side files committed
directly onto the source branch. Thin adapters over the
:mod:`propstore.source.common` owner functions.
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit_success
from propstore.cli.source import source
from propstore.source.common import commit_source_metadata, commit_source_notes


@source.command("write-notes")
@click.argument("name")
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Markdown notes file to commit as notes.md.",
)
@click.pass_obj
def write_notes(obj: CliContext, name: str, file_path: Path) -> None:
    """Write a source branch's notes.md from a file."""
    repo = require_repo(obj)
    sha = commit_source_notes(repo, name, file_path)
    emit_success(f"Wrote notes to source/{name} ({sha[:12]})")


@source.command("write-metadata")
@click.argument("name")
@click.option(
    "--file",
    "file_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSON metadata file to commit as metadata.json.",
)
@click.pass_obj
def write_metadata(obj: CliContext, name: str, file_path: Path) -> None:
    """Write a source branch's metadata.json from a file."""
    repo = require_repo(obj)
    sha = commit_source_metadata(repo, name, file_path)
    emit_success(f"Wrote metadata to source/{name} ({sha[:12]})")
