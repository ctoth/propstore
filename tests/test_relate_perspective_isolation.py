from __future__ import annotations

import asyncio
import sqlite3
from sqlite3 import Connection

import pytest


def _claim_db() -> Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE claim_core (id TEXT PRIMARY KEY, source_paper TEXT)")
    conn.execute(
        "CREATE TABLE claim_text_payload (claim_id TEXT PRIMARY KEY, auto_summary TEXT, statement TEXT, expression TEXT)"
    )
    conn.executemany(
        "INSERT INTO claim_core (id, source_paper) VALUES (?, ?)",
        [("claim-a", "paper-a"), ("claim-b", "paper-b")],
    )
    conn.executemany(
        "INSERT INTO claim_text_payload (claim_id, statement) VALUES (?, ?)",
        [("claim-a", "A says alpha."), ("claim-b", "B says beta.")],
    )
    return conn


def test_relate_perspective_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore.families.claims.declaration import (
        select_all_claim_ids,
        select_claim_text,
        select_claim_texts,
    )
    from propstore.heuristic import relate

    conn = _claim_db()

    def find_similar(_conn: Connection, claim_id: str, _model_name: str, *, top_k: int) -> list[dict]:
        if claim_id == "claim-a":
            return [{"id": "claim-b", "distance": 0.3}]
        if claim_id == "claim-b":
            return [{"id": "claim-a", "distance": 0.4}]
        return []

    async def classify_stance_async(
        claim_a: dict,
        claim_b: dict,
        *_args: object,
        **_kwargs: object,
    ) -> list[dict]:
        return [
            {
                "target": claim_b["id"],
                "type": "supports",
                "strength": "strong",
                "note": "forward",
                "conditions_differ": None,
                "resolution": {},
            },
            {
                "target": claim_a["id"],
                "type": "undercuts",
                "strength": "weak",
                "note": "reverse",
                "conditions_differ": None,
                "resolution": {},
            },
        ]

    class Store:
        def load_embedding_extension(self) -> None:
            pass

        def get_registered_models(self) -> list[dict]:
            return [{"model_name": "embedder"}]

        def get_claim_text(self, claim_id: str) -> dict | None:
            return select_claim_text(conn, claim_id)

        def get_claim_texts(self, claim_ids: list[str]) -> dict[str, dict]:
            return select_claim_texts(conn, claim_ids)

        def all_claim_ids(self) -> list[str]:
            return select_all_claim_ids(conn)

        def find_similar(
            self,
            claim_id: str,
            model_name: str,
            *,
            top_k: int,
        ) -> list[dict]:
            return find_similar(conn, claim_id, model_name, top_k=top_k)

    monkeypatch.setattr(relate, "classify_stance_async", classify_stance_async)

    result = asyncio.run(
        relate.relate_all_async(
            Store(),
            model_name="classifier",
            embedding_model=None,
            top_k=1,
            concurrency=1,
            on_progress=None,
        )
    )

    forward = result["stances_by_claim"]["claim-a"][0]
    reverse = result["stances_by_claim"]["claim-b"][0]
    assert forward["target"] == "claim-b"
    assert reverse["target"] == "claim-a"
    assert forward["perspective_source_claim_id"] == "claim-a"
    assert reverse["perspective_source_claim_id"] == "claim-b"
    assert forward["perspective_source_claim_id"] != reverse["perspective_source_claim_id"]
