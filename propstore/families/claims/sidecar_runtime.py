"""Claim derived-store runtime operations."""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from propstore.families.claims.declaration import (
    select_all_claim_ids,
    select_claim_text,
    select_claim_texts,
)


def embed_claims_for_request(
    sidecar: Path,
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
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    ids = [claim_id] if claim_id else None
    reports: list[tuple[str, Any]] = []
    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        load_vec_extension(conn)
        if model == "all":
            models = get_registered_models(conn)
            if not models:
                raise LookupError("no models registered")
            for model_row in models:
                model_name = str(model_row["model_name"])
                result = embed_claims(
                    conn,
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
                conn,
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
        conn.commit()
    return reports


def find_similar_claim_rows(
    sidecar: Path,
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
        load_vec_extension,
    )
    from quire.derived_runtime import connect_sqlite_store

    conn = connect_sqlite_store(sidecar)
    conn.row_factory = sqlite3.Row
    load_vec_extension(conn)

    try:
        if agree:
            rows = find_similar_agree(conn, claim_id, top_k=top_k)
        elif disagree:
            rows = find_similar_disagree(conn, claim_id, top_k=top_k)
        else:
            selected_model = model
            if selected_model is None:
                models = get_registered_models(conn)
                if not models:
                    raise LookupError("no embeddings found")
                selected_model = str(models[0]["model_name"])
            rows = find_similar(conn, claim_id, selected_model, top_k=top_k)
    finally:
        conn.close()

    return [dict(row) for row in rows]


class SidecarClaimRelationStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def load_embedding_extension(self) -> None:
        from propstore.families.embeddings.declaration import load_vec_extension

        load_vec_extension(self._conn)

    def get_registered_models(self) -> list[dict]:
        from propstore.families.embeddings.declaration import get_registered_models

        return get_registered_models(self._conn)

    def get_claim_text(self, claim_id: str) -> dict[str, Any] | None:
        return select_claim_text(self._conn, claim_id)

    def get_claim_texts(self, claim_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        return select_claim_texts(self._conn, claim_ids)

    def all_claim_ids(self) -> list[str]:
        return select_all_claim_ids(self._conn)

    def find_similar(
        self,
        claim_id: str,
        model_name: str,
        *,
        top_k: int,
    ) -> list[dict[str, Any]]:
        from propstore.families.embeddings.declaration import find_similar

        return find_similar(self._conn, claim_id, model_name, top_k=top_k)


def relate_claim_from_sidecar(
    sidecar: Path,
    claim_id: str,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_claim

    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_claim(
            SidecarClaimRelationStore(conn),
            claim_id,
            model_name,
            embedding_model,
            top_k,
        )


def relate_all_from_sidecar(
    sidecar: Path,
    model_name: str,
    embedding_model: str | None = None,
    top_k: int = 5,
    concurrency: int = 20,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    from quire.derived_runtime import connect_sqlite_store
    from propstore.heuristic.relate import relate_all

    conn = connect_sqlite_store(sidecar)
    with contextlib.closing(conn):
        conn.row_factory = sqlite3.Row
        return relate_all(
            SidecarClaimRelationStore(conn),
            model_name,
            embedding_model,
            top_k,
            concurrency=concurrency,
            on_progress=on_progress,
        )
