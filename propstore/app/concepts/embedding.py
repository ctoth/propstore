from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .mutation import (
    ConceptEmbedReport,
    ConceptEmbedModelReport,
    ConceptEmbedRequest,
    ConceptEmbeddingModelError,
    ConceptSidecarMissingError,
    ConceptSimilarHit,
    ConceptSimilarReport,
    ConceptSimilarRequest,
    ConceptWorkflowError,
    UnknownConceptError,
    _concept_embed_model_report,
    _require_sidecar,
)
from propstore.families.concepts.sidecar_runtime import (
    embed_concepts_for_request,
    find_similar_concept_rows,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


def embed_concept_embeddings(
    repo: Repository,
    request: ConceptEmbedRequest,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> ConceptEmbedReport:
    if not request.concept_id and not request.embed_all:
        raise ConceptWorkflowError("provide a concept ID or request all concepts")

    sidecar = _require_sidecar(repo)
    try:
        results = embed_concepts_for_request(
            sidecar,
            concept_id=request.concept_id,
            embed_all=request.embed_all,
            model=request.model,
            batch_size=request.batch_size,
            on_progress=on_progress,
        )
    except LookupError as exc:
        raise ConceptEmbeddingModelError(
            "no models registered. Run embed with a specific model first."
        ) from exc
    reports = [
        _concept_embed_model_report(model_name, result)
        for model_name, result in results
    ]
    return ConceptEmbedReport(results=tuple(reports))


def find_similar_concepts(
    repo: Repository,
    request: ConceptSimilarRequest,
) -> ConceptSimilarReport:
    sidecar = _require_sidecar(repo)
    try:
        rows = find_similar_concept_rows(
            sidecar,
            concept_id=request.concept_id,
            model=request.model,
            top_k=request.top_k,
            agree=request.agree,
            disagree=request.disagree,
        )
    except LookupError as exc:
        raise ConceptEmbeddingModelError(
            "no embeddings found. Run 'pks concept embed' first."
        ) from exc
    except ValueError as exc:
        raise ConceptWorkflowError(str(exc)) from exc

    return ConceptSimilarReport(
        hits=tuple(
            ConceptSimilarHit(
                distance=float(row.get("distance", 0)),
                concept_id=str(row.get("primary_logical_id") or row.get("id", "?")),
                canonical_name=str(row.get("canonical_name", "")),
                definition=str(row.get("definition") or ""),
            )
            for row in rows
        )
    )
