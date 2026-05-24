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
)
from propstore.compiler.workflows import build_repository_world_store
from propstore.families.concepts.sidecar_runtime import (
    embed_concepts_for_request,
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

    derived_store, _rebuilt = build_repository_world_store(repo)
    if not derived_store.path.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    try:
        results = embed_concepts_for_request(
            derived_store,
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
    derived_store, _rebuilt = build_repository_world_store(repo)
    if not derived_store.path.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    try:
        if request.agree:
            from propstore.families.embeddings.declaration import (
                find_similar_concepts_agree,
            )

            similarity_hits = find_similar_concepts_agree(
                derived_store,
                request.concept_id,
                top_k=request.top_k,
            )
        elif request.disagree:
            from propstore.families.embeddings.declaration import (
                find_similar_concepts_disagree,
            )

            similarity_hits = find_similar_concepts_disagree(
                derived_store,
                request.concept_id,
                top_k=request.top_k,
            )
        else:
            from propstore.world.model import WorldQuery

            with WorldQuery(derived_store=derived_store) as world:
                similarity_hits = world.similar_concepts(
                    request.concept_id,
                    request.model,
                    top_k=request.top_k,
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
                distance=hit.distance,
                concept_id=str(hit.primary_logical_id or hit.concept_id),
                canonical_name=hit.canonical_name or "",
                definition=hit.definition or "",
            )
            for hit in similarity_hits
        )
    )
