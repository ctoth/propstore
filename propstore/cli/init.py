"""pks init - bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit

from propstore.app.project_init import ProjectInitError, initialize_project


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: dict, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates a store-only propstore repository and commits the packaged
    default forms and concepts into the git store. Loose semantic files are
    written only by ``pks materialize``.
    If no DIRECTORY argument is given, creates a ``knowledge/`` directory
    in the current working directory.
    """
    context_obj = {} if obj is None else obj
    start = context_obj.get("start")
    root = (start / directory if start is not None else Path(directory)).resolve()

    try:
        report = initialize_project(root)
    except ProjectInitError as exc:
        raise click.ClickException(str(exc)) from exc

    if not report.initialized:
        emit(f"Already initialized: {report.root}")
        return

    emit(f"Initialized store-only propstore project at {report.root}/")
    emit("Seeded default forms and concepts in the git store.")
