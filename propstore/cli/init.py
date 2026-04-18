"""pks init - bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.project_init import ProjectInitError, initialize_project


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: dict, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates the standard knowledge tree (concepts/, claims/, contexts/,
    forms/, justifications/, predicates/, rules/, sidecar/, sources/,
    stances/, worldlines/) as a git-backed repository, and seeds the
    packaged default forms.
    If no DIRECTORY argument is given, creates a ``knowledge/`` directory
    in the current working directory.
    """
    context_obj = {} if obj is None else obj
    start = context_obj.get("start")
    root = start / directory if start is not None else Path(directory)

    try:
        report = initialize_project(root)
    except ProjectInitError as exc:
        raise click.ClickException(str(exc)) from exc

    if not report.initialized:
        click.echo(f"Already initialized: {report.root}")
        return

    click.echo(f"Initialized propstore project at {report.root}/")
    for path in report.paths:
        click.echo(f"  {path}/")
