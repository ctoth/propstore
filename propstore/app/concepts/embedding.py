from __future__ import annotations

from collections.abc import Callable
import contextlib
import sqlite3
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
    _resolve_sidecar_concept_id,
)
from propstore.sidecar.sqlite import connect_sidecar

if TYPE_CHECKING:
    from propstore.repository import Repository


def embed_concept_embeddings(
    repo: Repository,
    request: ConceptEmbedRequest,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> ConceptEmbedReport:
    if not request.concept_id and not request.embed_all:
        raise ConceptWorkflowError("provide a concept ID or use --all")

    from propstore.heuristic.embed import (
        _load_vec_extension,
        embed_concepts,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    reports: list[ConceptEmbedModelReport] = []
    conn = connect_sidecar(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        _load_vec_extension(conn)
        ids = (
            [_resolve_sidecar_concept_id(conn, request.concept_id)]
            if request.concept_id
            else None
        )

        if request.model == "all":
            models = get_registered_models(conn)
            if not models:
                raise ConceptEmbeddingModelError(
                    "no models registered. Run embed with a specific model first."
                )
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_concepts(
                    conn,
                    model_name,
                    concept_ids=ids,
                    batch_size=request.batch_size,
                    on_progress=(
                        None
                        if on_progress is None
                        else lambda done, total, model_name=model_name: on_progress(
                            model_name,
                            done,
                            total,
                        )
                    ),
                )
                reports.append(_concept_embed_model_report(model_name, result))
        else:
            result = embed_concepts(
                conn,
                request.model,
                concept_ids=ids,
                batch_size=request.batch_size,
                on_progress=(
                    None
                    if on_progress is None
                    else lambda done, total: on_progress(request.model, done, total)
                ),
            )
            reports.append(_concept_embed_model_report(request.model, result))
        conn.commit()
    return ConceptEmbedReport(results=tuple(reports))


def find_similar_concepts(
    repo: Repository,
    request: ConceptSimilarRequest,
) -> ConceptSimilarReport:
    from propstore.heuristic.embed import (
        _load_vec_extension,
        find_similar_concepts as find_similar_concepts_for_model,
        find_similar_concepts_agree,
        find_similar_concepts_disagree,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    conn = connect_sidecar(sidecar)
    conn.row_factory = sqlite3.Row
    _load_vec_extension(conn)

    try:
        resolved_id = _resolve_sidecar_concept_id(conn, request.concept_id)
        if request.agree:
            rows = find_similar_concepts_agree(conn, resolved_id, top_k=request.top_k)
        elif request.disagree:
            rows = find_similar_concepts_disagree(
                conn, resolved_id, top_k=request.top_k
            )
        else:
            model = request.model
            if model is None:
                models = get_registered_models(conn)
                if not models:
                    raise ConceptEmbeddingModelError(
                        "no embeddings found. Run 'pks concept embed' first."
                    )
                model = str(models[0]["model_name"])
            rows = find_similar_concepts_for_model(
                conn,
                resolved_id,
                model,
                top_k=request.top_k,
            )
    except ValueError as exc:
        raise ConceptWorkflowError(str(exc)) from exc
    finally:
        conn.close()

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
