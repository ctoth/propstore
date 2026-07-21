"""``pks claim embed`` / ``pks claim similar`` — embedding adapters.

Thin Click adapters over the embedding owner layer
(:mod:`propstore.families.embeddings.declaration` +
:meth:`propstore.world.WorldQuery.similar_claims`). ``embed`` requires the
``[embeddings]`` extra; an absent extra surfaces as a clean CLI failure rather
than a traceback. Similarity is a heuristic signal — each hit prints its distance
as a score and an empty result is reported honestly, never fabricated.
"""

from __future__ import annotations

import click

from propstore.cli.claim import claim, open_world
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table


@claim.command("embed")
@click.option("--model", "model_name", required=True, help="litellm embedding model.")
@click.pass_obj
def claim_embed(obj: CliContext, model_name: str) -> None:
    """Generate and store embeddings for every claim (requires propstore[embeddings])."""

    from propstore.families.embeddings.declaration import embed_claims_at

    repo = require_repo(obj)
    with open_world(repo) as world:
        claims = list(world.claims_for(None))
        path = world.sidecar_path
    try:
        report = embed_claims_at(path, claims, model_name)
    except ImportError as exc:
        fail(str(exc))
    emit(
        f"Embedded {report['embedded']}, skipped {report['skipped']}, "
        f"errors {report['errors']} (model {model_name})."
    )


@claim.command("similar")
@click.argument("claim_id")
@click.option(
    "--model",
    "model_name",
    default=None,
    help="Embedding model (default: first registered).",
)
@click.option("--top-k", "top_k", type=int, default=10, help="Number of neighbours.")
@click.pass_obj
def claim_similar(
    obj: CliContext, claim_id: str, model_name: str | None, top_k: int
) -> None:
    """List the claims most similar to CLAIM_ID by embedding distance."""

    repo = require_repo(obj)
    with open_world(repo) as world:
        hits = world.similar_claims(claim_id, model_name=model_name, top_k=top_k)
    if not hits:
        emit(f"No similar claims for {claim_id}.")
        return
    emit_table(
        ("Claim", "Distance", "Statement"),
        [
            (str(hit.claim_id), f"{hit.distance:.4f}", hit.statement or "")
            for hit in hits
        ],
    )
