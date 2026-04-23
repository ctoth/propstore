"""pks sidecar - sidecar inspection commands."""

from __future__ import annotations

import click

from propstore.app.compiler import SidecarQueryError, SidecarQueryRequest, query_sidecar
from propstore.cli.helpers import fail
from propstore.cli.output import emit
from propstore.repository import Repository


@click.group()
def sidecar() -> None:
    """Inspect compiled sidecar artifacts."""


@sidecar.command("query")
@click.argument("sql")
@click.pass_obj
def query(obj: dict, sql: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    repo: Repository = obj["repo"]
    try:
        result = query_sidecar(repo, SidecarQueryRequest(sql=sql))
    except FileNotFoundError:
        fail("Sidecar not found. Run 'pks build' first.")
    except SidecarQueryError as exc:
        fail(f"SQL error: {exc}")

    if not result.rows:
        emit("(no results)")
        return
    emit("\t".join(result.columns))
    for row in result.rows:
        emit("\t".join(row))
