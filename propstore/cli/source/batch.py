"""Source-branch batch ingestion: concepts / claims / justifications / stances.

Each command ingests a batch YAML file through the matching
``commit_source_*_batch`` owner. These adapters do not auto-finalize: finalize is
a separate workflow step (``pks source finalize``), and the CLI must not own
finalize semantics (CLAUDE.md "CLI adapter discipline").
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit_success
from propstore.cli.source import source
from propstore.source.claims import commit_source_claims_batch
from propstore.source.concepts import commit_source_concepts_batch
from propstore.source.relations import (
    commit_source_justifications_batch,
    commit_source_stances_batch,
)

_BATCH_FILE = click.option(
    "--batch",
    "batch_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Batch YAML file to ingest.",
)
_READER = click.option("--reader", default=None, help="Who extracted these (name or model id).")
_METHOD = click.option("--method", default=None, help="Extraction method (skill name, 'manual', …).")


@source.command("add-concepts")
@click.argument("name")
@_BATCH_FILE
@click.pass_obj
def add_concepts(obj: CliContext, name: str, batch_file: Path) -> None:
    """Ingest a concepts-batch YAML onto a source branch."""
    repo = require_repo(obj)
    sha = commit_source_concepts_batch(repo, name, batch_file)
    emit_success(f"Wrote concepts to source/{name} ({sha[:12]})")


@source.command("add-claim")
@click.argument("name")
@_BATCH_FILE
@_READER
@_METHOD
@click.option(
    "--context",
    "default_context",
    default=None,
    help="Default context id for claims with no inline context (inline wins).",
)
@click.pass_obj
def add_claim(
    obj: CliContext,
    name: str,
    batch_file: Path,
    reader: str | None,
    method: str | None,
    default_context: str | None,
) -> None:
    """Ingest a claims-batch YAML onto a source branch."""
    repo = require_repo(obj)
    sha = commit_source_claims_batch(
        repo,
        name,
        batch_file,
        reader=reader,
        method=method,
        default_context=default_context,
    )
    emit_success(f"Wrote claims to source/{name} ({sha[:12]})")


@source.command("add-justification")
@click.argument("name")
@_BATCH_FILE
@_READER
@_METHOD
@click.pass_obj
def add_justification(
    obj: CliContext, name: str, batch_file: Path, reader: str | None, method: str | None
) -> None:
    """Ingest a justifications-batch YAML onto a source branch."""
    repo = require_repo(obj)
    sha = commit_source_justifications_batch(
        repo, name, batch_file, reader=reader, method=method
    )
    emit_success(f"Wrote justifications to source/{name} ({sha[:12]})")


@source.command("add-stance")
@click.argument("name")
@_BATCH_FILE
@_READER
@_METHOD
@click.pass_obj
def add_stance(
    obj: CliContext, name: str, batch_file: Path, reader: str | None, method: str | None
) -> None:
    """Ingest a stances-batch YAML onto a source branch."""
    repo = require_repo(obj)
    sha = commit_source_stances_batch(repo, name, batch_file, reader=reader, method=method)
    emit_success(f"Wrote stances to source/{name} ({sha[:12]})")
