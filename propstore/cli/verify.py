"""pks verify - semantic verification commands."""

from __future__ import annotations

import click

from propstore.artifacts.codecs import render_yaml_value
from propstore.artifacts.codes import verify_claim_tree
from propstore.repository import Repository


@click.group()
def verify() -> None:
    """Verify semantic artifact trees and provenance."""


@verify.command("tree")
@click.argument("claim_ref")
@click.option("--commit", default=None)
@click.pass_obj
def verify_tree(obj: dict, claim_ref: str, commit: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        report = verify_claim_tree(repo, claim_ref, commit=commit)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_yaml_value(report))
