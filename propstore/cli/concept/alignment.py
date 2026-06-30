"""``pks concept`` alignment-lifecycle command adapters.

``align`` / ``decide`` / ``promote`` over the repository-bound alignment lifecycle
in :mod:`propstore.source.alignment`. These are the propose→decide→promote steps:
``align`` records a proposal artifact (no source mutation), ``decide`` records an
accept/reject decision, and ``promote`` is the single proposal→source boundary.
The adapters parse flags into the owner-function arguments and render the returned
:class:`~propstore.families.alignment.ConceptAlignmentArtifact`; the alignment math
and storage semantics live in the owner module.
"""
from __future__ import annotations

import click

from propstore.cli.concept import concept
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_success
from propstore.source.alignment import (
    align_sources,
    decide_alignment,
    promote_alignment,
)


@concept.command("align")
@click.option(
    "--sources",
    "sources",
    multiple=True,
    required=True,
    help="A source branch to align (repeat for each, e.g. --sources source/a).",
)
@click.pass_obj
def concept_align(obj: CliContext, sources: tuple[str, ...]) -> None:
    """Propose a concept alignment across several source branches."""

    repo = require_repo(obj)
    artifact = align_sources(repo, list(sources))
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
    """Promote an accepted alignment alternative into a canonical concept."""

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
