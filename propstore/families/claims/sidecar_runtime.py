"""Claim derived-store runtime operations."""

from __future__ import annotations

import contextlib
import sqlite3
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


def find_similar_claim_rows(
    derived_store: DerivedStoreHandle,
    *,
    claim_id: str,
    model: str | None,
    top_k: int,
    agree: bool = False,
    disagree: bool = False,
) -> list[dict[str, Any]]:
    from propstore.families.embeddings.declaration import (
        find_similar,
        find_similar_agree,
        find_similar_disagree,
        get_registered_models,
    )

    if agree:
        rows = find_similar_agree(derived_store, claim_id, top_k=top_k)
    elif disagree:
        rows = find_similar_disagree(derived_store, claim_id, top_k=top_k)
    else:
        selected_model = model
        if selected_model is None:
            models = get_registered_models(derived_store)
            if not models:
                raise LookupError("no embeddings found")
            selected_model = str(models[0]["model_name"])
        rows = find_similar(derived_store, claim_id, selected_model, top_k=top_k)

    return [dict(row) for row in rows]


class SidecarClaimRelationStore:
    def __init__(self, conn: sqlite3.Connection, derived_store: DerivedStoreHandle) -> None:
        self._conn = conn
        self._derived_store = derived_store

    def load_embedding_extension(self) -> None:
        return None

    def get_registered_models(self) -> list[dict]:
        from propstore.families.embeddings.declaration import get_registered_models

        return get_registered_models(self._derived_store)

    def get_claim_text(self, claim_id: str) -> dict[str, Any] | None:
        return self.get_claim_texts((claim_id,)).get(claim_id)

    def get_claim_texts(self, claim_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        if not claim_ids:
            return {}
        schema = world_sqlalchemy_schema()
        claim = schema.table("claim_core")
        text = schema.table("claim_text_payload")
        statement = (
            select(
                claim.c.id,
                text.c.auto_summary,
                text.c.statement,
                text.c.expression,
                claim.c.source_paper,
            )
            .select_from(
                claim.outerjoin(text, text.c.claim_id == claim.c.id)
            )
            .where(claim.c.id.in_(tuple(claim_ids)))
        )
        with self._derived_store.readonly_session(schema) as derived:
            rows = derived.execute(statement).mappings().all()
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            decoded = dict(row)
            decoded["text"] = (
                decoded.get("auto_summary")
                or decoded.get("statement")
                or decoded.get("expression")
                or decoded["id"]
            )
            result[str(decoded["id"])] = decoded
        return result

    def all_claim_ids(self) -> list[str]:
        schema = world_sqlalchemy_schema()
        claim = schema.table("claim_core")
        with self._derived_store.readonly_session(schema) as derived:
            rows = derived.execute(select(claim.c.id)).all()
        return [str(row[0]) for row in rows]

    def find_similar(
        self,
        claim_id: str,
        model_name: str,
        *,
        top_k: int,
    ) -> list[dict[str, Any]]:
        from propstore.families.embeddings.declaration import find_similar

        return find_similar(self._derived_store, claim_id, model_name, top_k=top_k)


def relate_claim_from_sidecar(
    derived_store: DerivedStoreHandle,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_claim

    conn = connect_sqlite_store(derived_store.path)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_claim(
            SidecarClaimRelationStore(conn, derived_store),
            claim_id,
            model_name,
            embedding_model,
            top_k,
        )


def relate_all_from_sidecar(
    derived_store: DerivedStoreHandle,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_all

    conn = connect_sqlite_store(derived_store.path)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_all(
            SidecarClaimRelationStore(conn, derived_store),
            model_name,
            embedding_model,
            top_k,
            concurrency=concurrency,
            on_progress=on_progress,
        )
