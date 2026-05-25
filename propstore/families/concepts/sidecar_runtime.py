"""Concept derived-store runtime operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quire.derived_store import DerivedStoreHandle
from propstore.families.registry import world_schema


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
    )

    reports: list[tuple[str, Any]] = []
    ids = None
    if concept_id:
        schema = world_schema()
        try:
            with derived_store.readonly_session(schema) as derived:
                resolved = schema.require_reference_id(
                    derived.session,
                    "concept",
                    concept_id,
                )
        except KeyError:
            raise ValueError(f"Unknown concept: {concept_id}")
        ids = [resolved]

    if model == "all":
        models = get_registered_models(derived_store)
        if not models:
            raise LookupError("no models registered")
        for model_row in models:
            model_name = str(model_row["model_name"])
            result = embed_concepts(
                derived_store,
                model_name,
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
            derived_store,
            model,
            concept_ids=ids,
            batch_size=batch_size,
            on_progress=(
                None
                if on_progress is None
                else lambda done, total: on_progress(model, done, total)
            ),
        )
        reports.append((model, result))
    return reports
