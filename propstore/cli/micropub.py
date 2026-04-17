"""pks micropub - inspect and lift micropublication bundles."""

from __future__ import annotations

import sys
from collections.abc import Iterator

import click

from propstore.artifacts.codecs import render_yaml_value
from propstore.artifacts.documents.micropubs import MicropublicationDocument
from propstore.artifacts.families import MICROPUBS_FILE_FAMILY
from propstore.artifacts.refs import MicropubsFileRef
from propstore.repository import Repository
from propstore.cli.helpers import EXIT_ERROR


@click.group()
def micropub() -> None:
    """Inspect micropublications."""


def _iter_micropubs(repo: Repository) -> Iterator[tuple[MicropubsFileRef, MicropublicationDocument]]:
    for ref in repo.artifacts.list(MICROPUBS_FILE_FAMILY):
        document = repo.artifacts.load(MICROPUBS_FILE_FAMILY, ref)
        if document is None:
            continue
        for entry in document.micropubs:
            yield ref, entry


def _find_micropub(
    repo: Repository,
    artifact_id: str,
) -> tuple[MicropubsFileRef, MicropublicationDocument] | None:
    for ref, entry in _iter_micropubs(repo):
        if entry.artifact_id == artifact_id:
            return ref, entry
    return None


@micropub.command("bundle")
@click.argument("source")
@click.pass_obj
def bundle(obj: dict, source: str) -> None:
    """Render the canonical micropublication bundle for a source."""
    repo: Repository = obj["repo"]
    document = repo.artifacts.load(MICROPUBS_FILE_FAMILY, MicropubsFileRef(source))
    if document is None:
        click.echo(f"Micropub bundle '{source}' not found.", err=True)
        sys.exit(EXIT_ERROR)
    click.echo(render_yaml_value(document.to_payload()).rstrip())


@micropub.command("show")
@click.argument("artifact_id")
@click.pass_obj
def show(obj: dict, artifact_id: str) -> None:
    """Render one micropublication by artifact id."""
    repo: Repository = obj["repo"]
    found = _find_micropub(repo, artifact_id)
    if found is None:
        click.echo(f"Micropub '{artifact_id}' not found.", err=True)
        sys.exit(EXIT_ERROR)
    _, entry = found
    click.echo(render_yaml_value(entry.to_payload()).rstrip())


@micropub.command("lift")
@click.argument("artifact_id")
@click.option("--target-context", required=True)
@click.pass_obj
def lift(obj: dict, artifact_id: str, target_context: str) -> None:
    """Report whether a micropublication can lift to a target context."""
    from propstore.context_types import loaded_contexts_to_lifting_system
    from propstore.validate_contexts import load_contexts

    repo: Repository = obj["repo"]
    found = _find_micropub(repo, artifact_id)
    if found is None:
        click.echo(f"Micropub '{artifact_id}' not found.", err=True)
        sys.exit(EXIT_ERROR)
    _, entry = found
    system = loaded_contexts_to_lifting_system(load_contexts(repo.tree() / "contexts"))
    source_context = entry.context.id
    if not system.can_lift(source_context, target_context):
        click.echo(f"not liftable: {artifact_id} {source_context} -> {target_context}")
        sys.exit(EXIT_ERROR)
    click.echo(f"liftable: {artifact_id} {source_context} -> {target_context}")
