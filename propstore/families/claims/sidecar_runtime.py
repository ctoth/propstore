"""Claim derived-store runtime operations."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import select

from quire.derived_store import DerivedStoreHandle
from propstore.families.world_charters import world_sqlalchemy_schema


def embed_claims_for_request(
    derived_store: DerivedStoreHandle,
    *,
    claim_id: str | None,
    embed_all: bool,
    model: str,
    batch_size: int,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[tuple[str, Any]]:
    if not claim_id and not embed_all:
        raise ValueError("provide a claim ID or request all claims")

    from propstore.families.embeddings.declaration import (
        embed_claims,
        get_registered_models,
    )

    ids = [claim_id] if claim_id else None
    reports: list[tuple[str, Any]] = []
    if model == "all":
        models = get_registered_models(derived_store)
        if not models:
            raise LookupError("no models registered")
        for model_row in models:
            model_name = str(model_row["model_name"])
            result = embed_claims(
                derived_store,
                model_name,
                claim_ids=ids,
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
        result = embed_claims(
            derived_store,
            model,
            claim_ids=ids,
            batch_size=batch_size,
            on_progress=(
                None
                if on_progress is None
                else lambda done, total: on_progress(model, done, total)
            ),
        )
        reports.append((model, result))
    return reports


def claim_texts_by_id(
    derived_store: DerivedStoreHandle,
    claim_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    if not claim_ids:
        return {}
    schema = world_sqlalchemy_schema()
    claim = schema.model("claim_core")
    with derived_store.readonly_session(schema) as derived:
        rows = tuple(
            derived.execute(
                select(claim).where(claim.id.in_(tuple(claim_ids)))
            ).scalars()
        )
        result: dict[str, dict[str, Any]] = {}
        for claim_model in rows:
            text_payload = claim_model.text_payload
            decoded = {
                "id": claim_model.id,
                "auto_summary": (
                    None if text_payload is None else text_payload.auto_summary
                ),
                "statement": None if text_payload is None else text_payload.statement,
                "expression": None if text_payload is None else text_payload.expression,
                "source_paper": claim_model.source_paper,
            }
            decoded["text"] = (
                decoded["auto_summary"]
                or decoded["statement"]
                or decoded["expression"]
                or decoded["id"]
            )
            result[str(claim_model.id)] = decoded
        return result


def claim_text_by_id(
    derived_store: DerivedStoreHandle,
    claim_id: str,
) -> dict[str, Any] | None:
    return claim_texts_by_id(derived_store, (claim_id,)).get(claim_id)


def all_claim_ids(derived_store: DerivedStoreHandle) -> tuple[str, ...]:
    schema = world_sqlalchemy_schema()
    claim = schema.model("claim_core")
    with derived_store.readonly_session(schema) as derived:
        return tuple(
            str(row[0])
            for row in derived.execute(select(claim.id)).all()
        )


def relate_claim_from_sidecar(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    from propstore.families.embeddings.declaration import (
        find_similar,
        get_registered_models,
    )
    from propstore.heuristic.relate import relate_claim

    return relate_claim(
        claim_id=claim_id,
        model_name=model_name,
        embedding_model=embedding_model,
        top_k=top_k,
        registered_models=lambda: get_registered_models(derived_store),
        claim_text=lambda selected_claim_id: claim_text_by_id(
            derived_store,
            selected_claim_id,
        ),
        similar_claims=lambda selected_claim_id, selected_model, selected_top_k: (
            find_similar(
                derived_store,
                selected_claim_id,
                selected_model,
                top_k=selected_top_k,
            )
        ),
    )


def relate_all_from_sidecar(
    derived_store: DerivedStoreHandle,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    from propstore.families.embeddings.declaration import (
        find_similar,
        get_registered_models,
    )
    from propstore.heuristic.relate import relate_all

    return relate_all(
        model_name=model_name,
        embedding_model=embedding_model,
        top_k=top_k,
        concurrency=concurrency,
        on_progress=on_progress,
        registered_models=lambda: get_registered_models(derived_store),
        all_claim_ids=lambda: all_claim_ids(derived_store),
        claim_texts=lambda claim_ids: claim_texts_by_id(derived_store, claim_ids),
        similar_claims=lambda selected_claim_id, selected_model, selected_top_k: (
            find_similar(
                derived_store,
                selected_claim_id,
                selected_model,
                top_k=selected_top_k,
            )
        ),
    )
