"""Tests for schema-driven bulk claim text fetching in relate sidecar runtime."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from quire.derived_store import DerivedStoreHandle

from propstore.families.claims.sidecar_runtime import SidecarClaimRelationStore
from tests.sidecar_schema_helpers import build_world_projection_schema


FIXTURE_CLAIMS = (
    ("c1", "paper_x", "Summary of c1", "Statement c1", None),
    ("c2", "paper_y", None, "Statement c2", "expr_c2"),
    ("c3", "paper_z", "Summary of c3", None, None),
    ("c4", "paper_x", None, None, "expr_c4"),
    ("c5", "paper_y", None, None, None),
)


@pytest.fixture
def store(tmp_path: Path) -> SidecarClaimRelationStore:
    sqlite_path = tmp_path / "sidecar.sqlite"
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    build_world_projection_schema(conn)
    for claim_id, paper, summary, statement, expression in FIXTURE_CLAIMS:
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, source_paper, provenance_page
            ) VALUES (?, ?, '[]', '', '', 0, 'measurement', ?, 1)
            """,
            (claim_id, claim_id, paper),
        )
        conn.execute(
            """
            INSERT INTO claim_text_payload (
                claim_id, auto_summary, statement, expression
            ) VALUES (?, ?, ?, ?)
            """,
            (claim_id, summary, statement, expression),
        )
    conn.commit()
    handle = DerivedStoreHandle(
        projection_id="propstore.world.test",
        source_commit="test",
        content_hash="test",
        cache_key="test",
        path=sqlite_path,
    )
    return SidecarClaimRelationStore(conn, handle)


def test_bulk_fetch_returns_requested_claim_texts(store: SidecarClaimRelationStore) -> None:
    result = store.get_claim_texts(("c1", "c3", "c5"))

    assert set(result) == {"c1", "c3", "c5"}
    assert result["c1"]["text"] == "Summary of c1"
    assert result["c3"]["text"] == "Summary of c3"
    assert result["c5"]["text"] == "c5"


def test_bulk_fetch_skips_missing_ids(store: SidecarClaimRelationStore) -> None:
    result = store.get_claim_texts(("c1", "missing", "c3"))

    assert set(result) == {"c1", "c3"}


def test_single_fetch_matches_bulk_fetch(store: SidecarClaimRelationStore) -> None:
    ids = ("c1", "c2", "c4")
    bulk = store.get_claim_texts(ids)

    individual = {
        claim_id: fetched
        for claim_id in ids
        if (fetched := store.get_claim_text(claim_id)) is not None
    }

    assert bulk == individual


def test_all_claim_ids_uses_schema_query(store: SidecarClaimRelationStore) -> None:
    assert store.all_claim_ids() == ["c1", "c2", "c3", "c4", "c5"]
