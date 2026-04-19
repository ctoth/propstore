"""Typed concept sidecar query and embedding workflows."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from propstore.repository import Repository


class ConceptWorkflowError(Exception):
    """Base class for expected concept workflow failures."""


class ConceptSidecarMissingError(ConceptWorkflowError):
    pass


class ConceptEmbeddingModelError(ConceptWorkflowError):
    pass


class UnknownConceptError(ConceptWorkflowError):
    def __init__(self, concept_id: str) -> None:
        super().__init__(f"Concept '{concept_id}' not found")
        self.concept_id = concept_id


@dataclass(frozen=True)
class ConceptSearchRequest:
    query: str
    limit: int = 20


@dataclass(frozen=True)
class ConceptSearchHit:
    logical_id: str
    canonical_name: str
    definition: str


@dataclass(frozen=True)
class ConceptSearchReport:
    hits: tuple[ConceptSearchHit, ...]


@dataclass(frozen=True)
class ConceptEmbedRequest:
    concept_id: str | None
    embed_all: bool
    model: str
    batch_size: int = 64


@dataclass(frozen=True)
class ConceptEmbedModelReport:
    model_name: str
    embedded: int
    skipped: int
    errors: int


@dataclass(frozen=True)
class ConceptEmbedReport:
    results: tuple[ConceptEmbedModelReport, ...]


@dataclass(frozen=True)
class ConceptSimilarRequest:
    concept_id: str
    model: str | None
    top_k: int
    agree: bool = False
    disagree: bool = False


@dataclass(frozen=True)
class ConceptSimilarHit:
    distance: float
    concept_id: str
    canonical_name: str
    definition: str


@dataclass(frozen=True)
class ConceptSimilarReport:
    hits: tuple[ConceptSimilarHit, ...]


def search_concepts(
    repo: Repository,
    request: ConceptSearchRequest,
) -> ConceptSearchReport:
    sidecar = _require_sidecar(repo)
    conn = sqlite3.connect(sidecar)
    with contextlib.closing(conn):
        rows = conn.execute(
            "SELECT concept.primary_logical_id, concept_fts.canonical_name, concept_fts.definition "
            "FROM concept_fts JOIN concept ON concept.id = concept_fts.concept_id "
            "WHERE concept_fts MATCH ? LIMIT ?",
            (request.query, request.limit),
        ).fetchall()
    return ConceptSearchReport(
        hits=tuple(
            ConceptSearchHit(
                logical_id=str(row[0]),
                canonical_name=str(row[1]),
                definition=str(row[2] or ""),
            )
            for row in rows
        )
    )


def embed_concept_embeddings(
    repo: Repository,
    request: ConceptEmbedRequest,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> ConceptEmbedReport:
    if not request.concept_id and not request.embed_all:
        raise ConceptWorkflowError("provide a concept ID or use --all")

    from propstore.embed import (
        _load_vec_extension,
        embed_concepts,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    reports: list[ConceptEmbedModelReport] = []
    conn = sqlite3.connect(sidecar)
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
    from propstore.embed import (
        _load_vec_extension,
        find_similar_concepts as find_similar_concepts_for_model,
        find_similar_concepts_agree,
        find_similar_concepts_disagree,
        get_registered_models,
    )

    sidecar = _require_sidecar(repo)
    conn = sqlite3.connect(sidecar)
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


def _resolve_sidecar_concept_id(conn: sqlite3.Connection, handle: str) -> str:
    conn.row_factory = sqlite3.Row
    direct = conn.execute("SELECT id FROM concept WHERE id = ?", (handle,)).fetchone()
    if direct is not None:
        return str(direct["id"])
    primary = conn.execute(
        "SELECT id FROM concept WHERE primary_logical_id = ?",
        (handle,),
    ).fetchone()
    if primary is not None:
        return str(primary["id"])
    canonical = conn.execute(
        "SELECT id FROM concept WHERE canonical_name = ?",
        (handle,),
    ).fetchone()
    if canonical is not None:
        return str(canonical["id"])
    alias = conn.execute(
        "SELECT concept_id FROM alias WHERE alias_name = ?",
        (handle,),
    ).fetchone()
    if alias is not None:
        return str(alias["concept_id"])
    raise UnknownConceptError(handle)


def _require_sidecar(repo: Repository) -> Path:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    return sidecar


def _concept_embed_model_report(
    model_name: str,
    result: Mapping[str, object],
) -> ConceptEmbedModelReport:
    return ConceptEmbedModelReport(
        model_name=model_name,
        embedded=_required_int(result, "embedded"),
        skipped=_required_int(result, "skipped"),
        errors=_required_int(result, "errors"),
    )


def _required_int(result: Mapping[str, object], key: str) -> int:
    value = result[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConceptWorkflowError(f"expected integer field '{key}'")
    return value
