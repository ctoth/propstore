"""pks verify - semantic verification commands."""

from __future__ import annotations

import click
import yaml

from propstore.artifact_codes import verify_claim_tree
from propstore.cli.repository import Repository


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
    click.echo(yaml.safe_dump(report, sort_keys=False, allow_unicode=True))
