from __future__ import annotations

import sys

import click

from propstore.source import (
    align_sources,
    decide_alignment,
    load_alignment_artifact,
    promote_alignment,
)
from propstore.cli.helpers import EXIT_ERROR
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
    artifact = align_sources(repo, [first_source, *extra_sources])
    click.echo(f"Created {artifact.id}")


@concept.command("query")
@click.argument("cluster_id")
@click.option("--mode", type=click.Choice(["skeptical", "credulous"]), default="credulous")
@click.option("--operator", type=click.Choice(["sum", "max", "leximax"]), default=None)
@click.pass_obj
def query_alignment(obj: dict, cluster_id: str, mode: str, operator: str | None) -> None:
    """Query an alignment artifact."""
    repo: Repository = obj["repo"]
    try:
        _, artifact = load_alignment_artifact(repo, cluster_id)
    except FileNotFoundError:
        click.echo(f"ERROR: Concept alignment '{cluster_id}' not found", err=True)
        sys.exit(EXIT_ERROR)

    if operator is not None:
        scores = artifact.queries.operator_scores.get(operator, {})
        for argument_id, score in sorted(scores.items()):
            click.echo(f"{argument_id}\t{score}")
        return

    accepted = (
        artifact.queries.skeptical_acceptance
        if mode == "skeptical"
        else artifact.queries.credulous_acceptance
    )
    for argument_id in accepted:
        click.echo(argument_id)


@concept.command("decide")
@click.argument("cluster_id")
@click.option("--accept", "accepted", multiple=True)
@click.option("--reject", "rejected", multiple=True)
@click.pass_obj
def decide_cmd(obj: dict, cluster_id: str, accepted: tuple[str, ...], rejected: tuple[str, ...]) -> None:
    """Persist accepted and rejected alternatives for an alignment artifact."""
    repo: Repository = obj["repo"]
    updated = decide_alignment(repo, cluster_id, accept=list(accepted), reject=list(rejected))
    click.echo(f"Updated {updated.id}")


@concept.command("promote")
@click.argument("cluster_id")
@click.pass_obj
def promote_cmd(obj: dict, cluster_id: str) -> None:
    """Promote an accepted alignment alternative into the canonical concept registry."""
    repo: Repository = obj["repo"]
    try:
        updated = promote_alignment(repo, cluster_id)
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(EXIT_ERROR)
    click.echo(f"Promoted {updated.id}")
