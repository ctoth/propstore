"""Tests for schema-driven bulk claim text fetching in relate sidecar runtime."""

from __future__ import annotations

from pathlib import Path

import pytest
from quire.derived_store import DerivedStoreHandle
from quire.sqlalchemy_store import create_sqlalchemy_store

from propstore.families.claims.types import ClaimType
from propstore.families.claims.sidecar_runtime import (
    all_claim_ids,
    claim_text_by_id,
    claim_texts_by_id,
)
from propstore.families.world_charters import world_record, world_sqlalchemy_schema


FIXTURE_CLAIMS = (
    ("c1", "paper_x", "Summary of c1", "Statement c1", None),
    ("c2", "paper_y", None, "Statement c2", "expr_c2"),
    ("c3", "paper_z", "Summary of c3", None, None),
    ("c4", "paper_x", None, None, "expr_c4"),
    ("c5", "paper_y", None, None, None),
)


@pytest.fixture
def handle(tmp_path: Path) -> DerivedStoreHandle:
    sqlite_path = tmp_path / "sidecar.sqlite"
    schema = world_sqlalchemy_schema()
    create_sqlalchemy_store(sqlite_path, schema)
    handle = DerivedStoreHandle(
        projection_id="propstore.world.test",
        source_commit="test",
        content_hash="test",
        cache_key="test",
        path=sqlite_path,
    )
    with handle.writable_session(schema) as derived:
        for seq, (claim_id, paper, summary, statement, expression) in enumerate(
            FIXTURE_CLAIMS
        ):
            derived.add(
                world_record(
                    "claim_core",
                    {
                        "id": claim_id,
                        "primary_logical_id": claim_id,
                        "logical_ids_json": "[]",
                        "version_id": "",
                        "content_hash": "",
                        "seq": seq,
                        "type": ClaimType.MEASUREMENT,
                        "source_paper": paper,
                        "provenance_page": 1,
                        "premise_kind": "ordinary",
                    },
                )
            )
            derived.add(
                world_record(
                    "claim_text_payload",
                    {
                        "claim_id": claim_id,
                        "statement": statement,
                        "expression": expression,
                        "auto_summary": summary,
                    },
                )
            )
        derived.commit()
    return handle


def test_bulk_fetch_returns_requested_claim_texts(handle: DerivedStoreHandle) -> None:
    result = claim_texts_by_id(handle, ("c1", "c3", "c5"))

    assert set(result) == {"c1", "c3", "c5"}
    assert result["c1"]["text"] == "Summary of c1"
    assert result["c3"]["text"] == "Summary of c3"
    assert result["c5"]["text"] == "c5"


def test_bulk_fetch_skips_missing_ids(handle: DerivedStoreHandle) -> None:
    result = claim_texts_by_id(handle, ("c1", "missing", "c3"))

    assert set(result) == {"c1", "c3"}


def test_single_fetch_matches_bulk_fetch(handle: DerivedStoreHandle) -> None:
    ids = ("c1", "c2", "c4")
    bulk = claim_texts_by_id(handle, ids)

    individual = {
        claim_id: fetched
        for claim_id in ids
        if (fetched := claim_text_by_id(handle, claim_id)) is not None
    }

    assert bulk == individual


def test_all_claim_ids_uses_schema_query(handle: DerivedStoreHandle) -> None:
    assert all_claim_ids(handle) == ("c1", "c2", "c3", "c4", "c5")
