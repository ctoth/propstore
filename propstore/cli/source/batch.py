"""Source batch ingestion commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.app.sources import (
    SourceBatchRequest,
    add_source_claims_batch,
    add_source_concepts_batch,
    add_source_justifications_batch,
    add_source_stances_batch,
)
from propstore.repository import Repository
from propstore.cli.source import source


@source.command("add-concepts")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def add_concepts(obj: dict, name: str, batch_file: Path) -> None:
    repo: Repository = obj["repo"]
    try:
        report = add_source_concepts_batch(
            repo,
            SourceBatchRequest(name=name, batch_file=batch_file),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote concepts to {report.branch}")
    click.echo(f"Auto-finalized {report.auto_finalized_branch}")


@source.command("add-claim")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these claims (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_claim(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        report = add_source_claims_batch(
            repo,
            SourceBatchRequest(
                name=name,
                batch_file=batch_file,
                reader=reader,
                method=method,
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote claims to {report.branch}")
    click.echo(f"Auto-finalized {report.auto_finalized_branch}")


@source.command("add-justification")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these justifications (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_justification(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        report = add_source_justifications_batch(
            repo,
            SourceBatchRequest(
                name=name,
                batch_file=batch_file,
                reader=reader,
                method=method,
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote justifications to {report.branch}")
    click.echo(f"Auto-finalized {report.auto_finalized_branch}")


@source.command("add-stance")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these stances (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_stance(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        report = add_source_stances_batch(
            repo,
            SourceBatchRequest(
                name=name,
                batch_file=batch_file,
                reader=reader,
                method=method,
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote stances to {report.branch}")
    click.echo(f"Auto-finalized {report.auto_finalized_branch}")
