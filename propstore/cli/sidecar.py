"""pks sidecar - sidecar inspection commands."""

from __future__ import annotations

import json

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
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def query(obj: dict, sql: str, fmt: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    repo: Repository = obj["repo"]
    try:
        result = query_sidecar(repo, SidecarQueryRequest(sql=sql))
    except FileNotFoundError:
        fail("Sidecar not found. Run 'pks build' first.")
    except SidecarQueryError as exc:
        fail(f"SQL error: {exc}")

    if fmt == "json":
        emit(json.dumps(result.to_json(), indent=2))
        return
    if not result.rows:
        emit("(no results)")
        return
    emit("\t".join(result.columns))
    for row in result.rows:
        emit("\t".join(row))
