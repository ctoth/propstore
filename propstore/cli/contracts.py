"""Contract manifest CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit, emit_success
from propstore.contracts import build_propstore_contract_manifest
from propstore.repository import Repository


@click.command("contract-manifest")
@click.option(
    "--write",
    is_flag=True,
    help="Materialize the contract schema to refs/propstore/schema.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check the freshly-built schema against the materialized ref.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write the manifest YAML to this path instead of stdout.",
)
@click.pass_obj
def contract_manifest(obj: dict, write: bool, check: bool, output: Path | None) -> None:
    """Render, materialize, or check the Propstore contract schema."""
    if write:
        repo: Repository = obj["repo"]
        repo.write_schema_ref()
        emit_success("Materialized contract schema to refs/propstore/schema")
        return
    if check:
        repo = obj["repo"]
        repo.check_schema_compatibility()
        emit_success("Contract schema is compatible with the materialized ref")
        return
    payload = build_propstore_contract_manifest().to_yaml()
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        emit_success(f"Wrote {output}")
        return
    emit(payload.decode("utf-8"), nl=False)
