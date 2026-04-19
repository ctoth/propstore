"""CLI command for committed-snapshot repository import."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.app.repository_import import RepositoryImportError, import_repository
from quire.documents import render_yaml_value


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
        result = import_repository(
            repo,
            source_repository,
            target_branch=target_branch,
            message=message,
        )
    except RepositoryImportError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_yaml_value(result))
