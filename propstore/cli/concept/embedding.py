from __future__ import annotations

import click

from propstore.cli.helpers import fail
from propstore.cli.output import emit

from propstore.cli.concept import (
    concept,
)


# ── concept embed ────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all concepts")
@click.option("--model", required=True, help="litellm model string, or 'all'")
@click.option("--batch-size", default=64, type=int, help="Concepts per API call")
@click.pass_obj
def embed(obj: dict, concept_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for concepts via litellm."""
    from propstore.app.concepts import (
        ConceptEmbedRequest,
        ConceptEmbeddingModelError,
        ConceptSidecarMissingError,
        ConceptWorkflowError,
        UnknownConceptError,
        embed_concept_embeddings,
    )

    def progress(model_name: str, done: int, total: int) -> None:
        if model == "all":
            if done % batch_size == 0:
                emit(f"  {done}/{total}", nl=False)
            return
        emit(f"  {done}/{total} concepts embedded", err=True)

    try:
        report = embed_concept_embeddings(
            obj["repo"],
            ConceptEmbedRequest(
                concept_id=concept_id,
                embed_all=embed_all,
                model=model,
                batch_size=batch_size,
            ),
            on_progress=progress,
        )
    except ConceptSidecarMissingError as exc:
        fail(exc)
    except (ConceptEmbeddingModelError, ConceptWorkflowError, UnknownConceptError) as exc:
        fail(exc)

    if model == "all":
        for result in report.results:
            emit(f"Embedding with {result.model_name}...")
            emit(
                f"  embedded={result.embedded} "
                f"skipped={result.skipped} "
                f"errors={result.errors}"
            )
        return

    result = report.results[0]
    emit(
        f"Embedded: {result.embedded}, "
        f"Skipped: {result.skipped}, "
        f"Errors: {result.errors}"
    )


# ── concept similar ──────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id")
@click.option("--model", default=None, help="litellm model string (default: first available)")
@click.option("--top-k", default=10, type=int, help="Number of results")
@click.option("--agree", is_flag=True, help="Similar under ALL stored models")
@click.option("--disagree", is_flag=True, help="Similar under some models but not others")
@click.pass_obj
def similar(obj: dict, concept_id: str, model: str | None, top_k: int, agree: bool, disagree: bool) -> None:
    """Find similar concepts by embedding distance."""
    from propstore.app.concepts import (
        ConceptEmbeddingModelError,
        ConceptSidecarMissingError,
        ConceptSimilarRequest,
        ConceptWorkflowError,
        UnknownConceptError,
        find_similar_concepts,
    )

    try:
        report = find_similar_concepts(
            obj["repo"],
            ConceptSimilarRequest(
                concept_id=concept_id,
                model=model,
                top_k=top_k,
                agree=agree,
                disagree=disagree,
            ),
        )
    except ConceptSidecarMissingError as exc:
        fail(exc)
    except (ConceptEmbeddingModelError, ConceptWorkflowError, UnknownConceptError) as exc:
        fail(exc)

    if not report.hits:
        emit("No similar concepts found.")
        return

    for hit in report.hits:
        definition = hit.definition[:80]
        emit(
            f"  {hit.distance:.4f}  "
            f"{hit.concept_id}  "
            f"{hit.canonical_name}  — {definition}"
        )
