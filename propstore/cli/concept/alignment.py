"""Presentation adapters for durable concept-alignment proposals."""

from __future__ import annotations

import click

from propstore.cli.concept import concept
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_success
from propstore.source.alignment import (
    align_repository_snapshots,
    decide_alignment,
    promote_alignment,
)
from propstore.source.stages import AlignRepositorySnapshotsRequest


@concept.command("align")
@click.option(
    "--imports",
    "import_branches",
    multiple=True,
    required=True,
    help="A committed repository-import branch to align; repeat for each branch.",
)
@click.pass_obj
def concept_align(obj: CliContext, import_branches: tuple[str, ...]) -> None:
    """Create an open alignment proposal over pinned imported KB snapshots."""

    repo = require_repo(obj)
    request = AlignRepositorySnapshotsRequest(import_branches=import_branches)
    try:
        artifact = align_repository_snapshots(repo, request)
    except (FileNotFoundError, ValueError) as exc:
        fail(str(exc))
    emit(f"Created alignment proposal {artifact.alignment_id}")


@concept.command("decide")
@click.argument("cluster_id")
@click.option("--accept", "accept", multiple=True, help="An alternative id to accept.")
@click.option("--reject", "reject", multiple=True, help="An alternative id to reject.")
@click.pass_obj
def concept_decide(
    obj: CliContext,
    cluster_id: str,
    accept: tuple[str, ...],
    reject: tuple[str, ...],
) -> None:
    """Record an accept/reject decision over an alignment proposal."""

    repo = require_repo(obj)
    try:
        artifact = decide_alignment(
            repo, cluster_id, accept=list(accept), reject=list(reject)
        )
    except FileNotFoundError:
        fail(f"Unknown alignment: {cluster_id}")
    emit_success(
        f"Decided alignment {artifact.alignment_id}: "
        f"accepted={list(artifact.decision.accepted)} "
        f"rejected={list(artifact.decision.rejected)}"
    )


@concept.command("promote")
@click.argument("cluster_id")
@click.pass_obj
def concept_promote(obj: CliContext, cluster_id: str) -> None:
    """Promote an explicitly accepted alternative."""

    repo = require_repo(obj)
    try:
        artifact = promote_alignment(repo, cluster_id)
    except FileNotFoundError:
        fail(f"Unknown alignment: {cluster_id}")
    except ValueError as exc:
        fail(str(exc))
    emit_success(
        f"Promoted alignment {artifact.alignment_id} -> "
        f"{artifact.decision.promoted_concept}"
    )
