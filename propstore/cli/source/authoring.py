"""Source authoring commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit

from propstore.app.sources import (
    SourceBatchRequest,
    write_source_metadata,
    write_source_notes,
)
from propstore.repository import Repository
from propstore.cli.source import source


@source.command("write-notes")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_notes(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    report = write_source_notes(
        repo,
        SourceBatchRequest(name=name, batch_file=file_path),
    )
    emit(f"Wrote notes to {report.branch}")


@source.command("write-metadata")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_metadata(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    report = write_source_metadata(
        repo,
        SourceBatchRequest(name=name, batch_file=file_path),
    )
    emit(f"Wrote metadata to {report.branch}")
