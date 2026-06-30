"""``pks init`` — bootstrap a new propstore knowledge repository.

A thin Click adapter over :func:`propstore.app.project_init.initialize_project`
(CLAUDE.md "CLI adapter discipline"): it resolves the target directory from the
argument and the root group's stored start dir, calls the owner core, renders the
typed report, and maps the expected :class:`ProjectInitError` to a Click error.
``init`` bypasses the repository lookup — the root group stores the start dir
under ``ctx.obj["start"]`` rather than a repository handle.
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.app.project_init import ProjectInitError, initialize_project
from propstore.cli.helpers import CliContext
from propstore.cli.output import emit


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: CliContext, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates a store-only propstore repository and commits the packaged default
    forms and concepts into the git store. Loose semantic files are written only
    by ``pks materialize``. With no DIRECTORY argument, creates a ``knowledge/``
    directory in the current working directory.
    """
    start = obj.get("start")
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
