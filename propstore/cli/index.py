"""pks index — subcommands for managing git index state."""

from __future__ import annotations

import click

from propstore.app.index import IndexWorkflowError, reset_index
from propstore.cli.helpers import fail
from propstore.cli.output import emit_success
from propstore.repository import Repository


@click.group()
def index() -> None:
    """Manage the working git index for a propstore knowledge repo."""


@index.command("reset")
@click.pass_obj
def reset(obj: dict) -> None:
    """Rewrite the git index to match HEAD, discarding staged entries.

    Recovers from the phantom-deletion pattern where ``pks source
    promote`` has synced the worktree but the user's git index still
    holds stale staged deletions from earlier operations. A subsequent
    plain ``git commit`` can otherwise silently wipe files.
    """
    repo: Repository = obj["repo"]
    try:
        report = reset_index(repo)
    except IndexWorkflowError as exc:
        fail(exc)

    emit_success(
        f"Reset index to HEAD ({report.head_sha[:8]}); cleared {report.cleared_entries} prior entries"
    )
