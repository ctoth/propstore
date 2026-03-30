"""CLI command for committed-snapshot repository import."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import click
import yaml

from propstore.repo.repo_import import commit_repo_import, plan_repo_import


@click.command("import-repo")
@click.argument("source_repo", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--target-branch", default=None, help="Branch that receives the import commit.")
@click.option("--message", default=None, help="Override the default import commit message.")
@click.pass_context
def import_repo_cmd(
    ctx: click.Context,
    source_repo: Path,
    target_branch: str | None,
    message: str | None,
) -> None:
    """Import a source repo's committed semantic tree onto a destination branch."""
    repo = ctx.obj["repo"]
    if repo.git is None:
        raise click.ClickException("import-repo requires a git-backed repository")

    plan = plan_repo_import(repo, source_repo, target_branch=target_branch)
    result = commit_repo_import(repo, plan, message=message)
    click.echo(yaml.safe_dump(asdict(result), sort_keys=False).rstrip())
