from __future__ import annotations

from collections.abc import Callable

import click

from propstore.app.claims import (
    ClaimEmbedRequest,
    ClaimEmbeddingModelError,
    ClaimSidecarMissingError,
    ClaimSimilarRequest,
    ClaimWorkflowError,
    embed_claim_embeddings,
    find_similar_claims,
)
from propstore.cli.claim import claim
from propstore.cli.helpers import fail
from propstore.cli.output import emit


def _claim_embed_progress_callback(
    model: str,
    batch_size: int,
) -> Callable[[str, int, int], None]:
    if model == "all":
        def report_model_progress(_model_name: str, done: int, total: int) -> None:
            if done % batch_size == 0 or done == total:
                emit(f"  {done}/{total}")

        return report_model_progress

    def report_claim_progress(_model_name: str, done: int, total: int) -> None:
        emit(f"  {done}/{total} claims embedded", err=True)

    return report_claim_progress


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "embed_all", is_flag=True, help="Embed all claims")
@click.option("--model", required=True, help="litellm model string, or 'all' for every registered model")
@click.option("--batch-size", default=64, type=int, help="Claims per API call")
@click.pass_obj
def embed(obj: dict, claim_id: str | None, embed_all: bool, model: str, batch_size: int) -> None:
    """Generate embeddings for claims via litellm."""
    repo = obj["repo"]
    try:
        report = embed_claim_embeddings(
            repo,
            ClaimEmbedRequest(
                claim_id=claim_id,
                embed_all=embed_all,
                model=model,
                batch_size=batch_size,
            ),
            on_progress=_claim_embed_progress_callback(model, batch_size),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except ClaimEmbeddingModelError as exc:
        fail(exc)
    except ClaimWorkflowError as exc:
        fail(exc)

    if model == "all":
        for result in report.results:
            emit(f"Embedding with {result.model_name}...")
            emit(f"  embedded={result.embedded} skipped={result.skipped} errors={result.errors}")
        return

    result = report.results[0]
    emit(f"Embedded: {result.embedded}, Skipped: {result.skipped}, Errors: {result.errors}")


@claim.command()
@click.argument("claim_id")
@click.option("--model", default=None, help="litellm model string (default: first available)")
@click.option("--top-k", default=10, type=int, help="Number of results")
@click.option("--agree", is_flag=True, help="Similar under ALL stored models")
@click.option("--disagree", is_flag=True, help="Similar under some models but not others")
@click.pass_obj
def similar(obj: dict, claim_id: str, model: str | None, top_k: int, agree: bool, disagree: bool) -> None:
    """Find similar claims by embedding distance."""
    repo = obj["repo"]
    try:
        report = find_similar_claims(
            repo,
            ClaimSimilarRequest(
                claim_id=claim_id,
                model=model,
                top_k=top_k,
                agree=agree,
                disagree=disagree,
            ),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except (ClaimEmbeddingModelError, ClaimWorkflowError) as exc:
        fail(exc)

    if not report.hits:
        emit("No similar claims found.")
        return

    for hit in report.hits:
        emit(f"  {hit.distance:.4f}  {hit.claim_id}  [{hit.source_paper}]  {hit.summary[:120]}")
