"""``pks contract-manifest`` — render or write the semantic-contract manifest.

A thin Click adapter (CLAUDE.md "CLI adapter discipline") over
:mod:`propstore.contracts`: it builds the manifest from code and either renders it
to stdout or writes it to the checked-in path / a chosen output path. No contract
assembly logic lives here.
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.output import emit, emit_success
from propstore.contracts import (
    CONTRACT_MANIFEST_PATH,
    build_propstore_contract_manifest,
    write_propstore_contract_manifest,
)


@click.command("contract-manifest")
@click.option("--write", is_flag=True, help="Write the checked-in manifest.")
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write the manifest to this path instead of stdout.",
)
def contract_manifest(write: bool, output: Path | None) -> None:
    """Render or write the Propstore contract manifest."""
    if write:
        path = write_propstore_contract_manifest(output or CONTRACT_MANIFEST_PATH)
        emit_success(f"Wrote {path}")
        return
    payload = build_propstore_contract_manifest().to_yaml()
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        emit_success(f"Wrote {output}")
        return
    emit(payload.decode("utf-8"), nl=False)
