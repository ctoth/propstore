"""``pks concept embed`` / ``pks concept similar`` — embedding adapters.

Thin Click adapters over the embedding owner layer
(:mod:`propstore.families.embeddings.declaration` +
:meth:`propstore.world.WorldQuery.similar_concepts`). ``embed`` requires the
``[embeddings]`` extra; an absent extra surfaces as a clean CLI failure.
Similarity is a heuristic signal — each hit prints its distance, empty is honest.
"""

from __future__ import annotations

import click

from propstore.cli.concept import concept, open_world
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table


@concept.command("embed")
@click.option("--model", "model_name", required=True, help="litellm embedding model.")
@click.pass_obj
def concept_embed(obj: CliContext, model_name: str) -> None:
    """Generate and store embeddings for every concept (requires propstore[embeddings])."""

    from propstore.families.embeddings.declaration import embed_concepts_at

    repo = require_repo(obj)
    with open_world(repo) as world:
        concepts = list(world.all_concepts())
        path = world.sidecar_path
    try:
        report = embed_concepts_at(path, concepts, model_name)
    except ImportError as exc:
        fail(str(exc))
    emit(
        f"Embedded {report['embedded']}, skipped {report['skipped']}, "
        f"errors {report['errors']} (model {model_name})."
    )


@concept.command("similar")
@click.argument("concept_id")
@click.option("--model", "model_name", default=None, help="Embedding model (default: first registered).")
@click.option("--top-k", "top_k", type=int, default=10, help="Number of neighbours.")
@click.pass_obj
def concept_similar(
    obj: CliContext, concept_id: str, model_name: str | None, top_k: int
) -> None:
    """List the concepts most similar to CONCEPT_ID by embedding distance."""

    repo = require_repo(obj)
    with open_world(repo) as world:
        hits = world.similar_concepts(concept_id, model_name=model_name, top_k=top_k)
    if not hits:
        emit(f"No similar concepts for {concept_id}.")
        return
    emit_table(
        ("Concept", "Distance", "Name"),
        [
            (str(hit.concept_id), f"{hit.distance:.4f}", hit.canonical_name or "")
            for hit in hits
        ],
    )
