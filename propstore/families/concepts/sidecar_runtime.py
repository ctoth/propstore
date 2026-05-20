"""Concept derived-store runtime operations."""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Callable
from typing import Any

from quire.derived_store import DerivedStoreHandle
from propstore.world import WorldQuery


def embed_concepts_for_request(
    derived_store: DerivedStoreHandle,
    *,
    concept_id: str | None,
    embed_all: bool,
    model: str,
    batch_size: int,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[tuple[str, Any]]:
    if not concept_id and not embed_all:
        raise ValueError("provide a concept ID or request all concepts")

    from propstore.families.embeddings.declaration import (
        embed_concepts,
        get_registered_models,
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    sidecar = derived_store.path
    reports: list[tuple[str, Any]] = []
    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        load_vec_extension(conn)
        ids = None
        if concept_id:
            resolved = WorldQuery(derived_store=derived_store).resolve_concept(concept_id)
            if resolved is None:
                raise ValueError(f"Unknown concept: {concept_id}")
            ids = [resolved]

        if model == "all":
            models = get_registered_models(conn)
            if not models:
                raise LookupError("no models registered")
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_concepts(
                    conn,
                    model_name,
                    derived_store=derived_store,
                    concept_ids=ids,
                    batch_size=batch_size,
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
                reports.append((model_name, result))
        else:
            result = embed_concepts(
                conn,
                model,
                derived_store=derived_store,
                concept_ids=ids,
                batch_size=batch_size,
                on_progress=(
                    None
                    if on_progress is None
                    else lambda done, total: on_progress(model, done, total)
                ),
            )
            reports.append((model, result))
        conn.commit()
    return reports


def find_similar_concept_rows(
    derived_store: DerivedStoreHandle,
    *,
    concept_id: str,
    model: str | None,
    top_k: int,
    agree: bool = False,
    disagree: bool = False,
) -> list[dict[str, Any]]:
    from propstore.families.embeddings.declaration import (
        find_similar_concepts,
        find_similar_concepts_agree,
        find_similar_concepts_disagree,
        get_registered_models,
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    sidecar = derived_store.path
    conn = connect_sqlite_store(sidecar)
    conn.row_factory = sqlite3.Row
    load_vec_extension(conn)

    try:
        resolved_id = WorldQuery(derived_store=derived_store).resolve_concept(concept_id)
        if resolved_id is None:
            raise ValueError(f"Unknown concept: {concept_id}")
        if agree:
            rows = find_similar_concepts_agree(
                conn,
                resolved_id,
                derived_store=derived_store,
                top_k=top_k,
            )
        elif disagree:
            rows = find_similar_concepts_disagree(
                conn,
                resolved_id,
                derived_store=derived_store,
                top_k=top_k,
            )
        else:
            selected_model = model
            if selected_model is None:
                models = get_registered_models(conn)
                if not models:
                    raise LookupError("no embeddings found")
                selected_model = str(models[0]["model_name"])
            rows = find_similar_concepts(
                conn,
                resolved_id,
                selected_model,
                derived_store=derived_store,
                top_k=top_k,
            )
    finally:
        conn.close()

    return [dict(row) for row in rows]
