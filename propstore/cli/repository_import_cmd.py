"""CLI command for committed-snapshot repository import."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import click

from quire.documents import render_yaml_value
from propstore.storage.repository_import import commit_repository_import, plan_repository_import


@click.command("import-repository")
@click.argument("source_repository", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--target-branch", default=None, help="Branch that receives the import commit.")
@click.option("--message", default=None, help="Override the default import commit message.")
@click.pass_context
def import_repository_cmd(
    ctx: click.Context,
    source_repository: Path,
    target_branch: str | None,
    message: str | None,
) -> None:
    """Import a source repository's committed semantic tree onto a destination branch."""
    repo = ctx.obj["repo"]
    try:
        repo.snapshot.head_sha()
    except ValueError as exc:
        raise click.ClickException("import-repository requires a git-backed repository") from exc

    plan = plan_repository_import(repo, source_repository, target_branch=target_branch)
    result = commit_repository_import(repo, plan, message=message)
    click.echo(render_yaml_value(asdict(result)))
