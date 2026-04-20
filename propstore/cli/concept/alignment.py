from __future__ import annotations

import click

from propstore.cli.output import emit

from propstore.app.concepts import (
    ConceptAlignmentBuildRequest,
    ConceptAlignmentDecisionRequest,
    ConceptAlignmentQueryRequest,
    ConceptDisplayError,
    build_concept_alignment,
    decide_concept_alignment,
    promote_concept_alignment,
    query_concept_alignment,
)
from propstore.repository import Repository
from propstore.cli.concept import (
    concept,
)


@concept.command("align")
@click.option("--sources", "first_source", required=True)
@click.argument("extra_sources", nargs=-1)
@click.pass_obj
def align_cmd(obj: dict, first_source: str, extra_sources: tuple[str, ...]) -> None:
    """Build and persist a concept-alignment artifact from source branches."""
    repo: Repository = obj["repo"]
    report = build_concept_alignment(
        repo,
        ConceptAlignmentBuildRequest(sources=(first_source, *extra_sources)),
    )
    emit(f"Created {report.alignment_id}")


@concept.command("query")
@click.argument("cluster_id")
@click.option("--mode", type=click.Choice(["skeptical", "credulous"]), default="credulous")
@click.option("--operator", type=click.Choice(["sum", "max", "leximax"]), default=None)
@click.pass_obj
def query_alignment(obj: dict, cluster_id: str, mode: str, operator: str | None) -> None:
    """Query an alignment artifact."""
    repo: Repository = obj["repo"]
    try:
        report = query_concept_alignment(
            repo,
            ConceptAlignmentQueryRequest(
                cluster_id=cluster_id,
                mode=mode,
                operator=operator,
            ),
        )
    except ConceptDisplayError as exc:
        raise click.ClickException(str(exc)) from exc

    if operator is not None:
        for score in report.scores:
            emit(f"{score.argument_id}\t{score.score}")
        return

    for argument_id in report.accepted_argument_ids:
        emit(argument_id)


@concept.command("decide")
@click.argument("cluster_id")
@click.option("--accept", "accepted", multiple=True)
@click.option("--reject", "rejected", multiple=True)
@click.pass_obj
def decide_cmd(obj: dict, cluster_id: str, accepted: tuple[str, ...], rejected: tuple[str, ...]) -> None:
    """Persist accepted and rejected alternatives for an alignment artifact."""
    repo: Repository = obj["repo"]
    report = decide_concept_alignment(
        repo,
        ConceptAlignmentDecisionRequest(
            cluster_id=cluster_id,
            accepted=accepted,
            rejected=rejected,
        ),
    )
    emit(f"Updated {report.alignment_id}")


@concept.command("promote")
@click.argument("cluster_id")
@click.pass_obj
def promote_cmd(obj: dict, cluster_id: str) -> None:
    """Promote an accepted alignment alternative into the canonical concept registry."""
    repo: Repository = obj["repo"]
    try:
        report = promote_concept_alignment(repo, cluster_id)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    emit(f"Promoted {report.alignment_id}")
