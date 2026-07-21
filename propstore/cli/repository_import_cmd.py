"""Click adapter for committed-snapshot repository import.

Thin wrapper over :mod:`propstore.importing.repository_import`: plans a
committed-snapshot import from a source repository and (unless ``--plan``)
commits it onto the destination's ``import/<name>`` branch, emitting the typed
result as YAML. No import logic lives here (CLAUDE.md "CLI adapter discipline").
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit_yaml
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)


@click.command("import-repository")
@click.argument(
    "source_repository",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--target-branch",
    default=None,
    help="Branch that receives the import commit (default: import/<name>).",
)
@click.option(
    "--message", default=None, help="Override the default import commit message."
)
@click.option(
    "--plan",
    "plan_only",
    is_flag=True,
    help="Plan the import and emit the planned writes/deletes without committing.",
)
@click.pass_obj
def import_repository_cmd(
    obj: CliContext,
    source_repository: Path,
    target_branch: str | None,
    message: str | None,
    plan_only: bool,
) -> None:
    """Import a source repository's committed semantic tree onto a destination branch."""
    repo = require_repo(obj)
    plan = plan_repository_import(repo, source_repository, target_branch=target_branch)
    if plan_only:
        emit_yaml(
            {
                "surface": "repository_import_plan",
                "source_repository": plan.source_repository,
                "source_commit": plan.source_commit,
                "target_branch": plan.target_branch,
                "repository_name": plan.repository_name,
                "writes": sorted(plan.writes),
                "deletes": list(plan.deletes),
                "touched_paths": list(plan.touched_paths),
                "warnings": list(plan.warnings),
            }
        )
        return
    result = commit_repository_import(repo, plan, message=message)
    emit_yaml(result)
