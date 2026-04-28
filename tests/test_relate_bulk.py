"""Tests for _bulk_get_claim_texts — bulk claim text fetching.

Verifies the bulk path is a faithful replacement for per-claim _get_claim_text.
"""

from __future__ import annotations

import sqlite3

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Fixture: in-memory DB with 5 claims
# ---------------------------------------------------------------------------

FIXTURE_CLAIMS = [
    ("c1", "concept_a", "paper_x", "Summary of c1", "Statement c1", None),
    ("c2", "concept_b", "paper_y", None, "Statement c2", "expr_c2"),
    ("c3", "concept_a", "paper_z", "Summary of c3", None, None),
    ("c4", None, "paper_x", None, None, "expr_c4"),
    ("c5", "concept_c", "paper_y", None, None, None),  # no text at all — falls back to id
]
FIXTURE_IDS = [c[0] for c in FIXTURE_CLAIMS]


@pytest.fixture
def conn():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            concept_id TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            branch TEXT
        );
        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            auto_summary TEXT,
            statement TEXT,
            expression TEXT
        );
    """)
    for cid, concept, paper, summary, stmt, expr in FIXTURE_CLAIMS:
        db.execute(
            "INSERT INTO claim_core (id, concept_id, source_paper) VALUES (?, ?, ?)",
            (cid, concept, paper),
        )
        db.execute(
            "INSERT INTO claim_text_payload (claim_id, auto_summary, statement, expression) VALUES (?, ?, ?, ?)",
            (cid, summary, stmt, expr),
        )
    db.commit()
    return db


# ---------------------------------------------------------------------------
# Example tests
# ---------------------------------------------------------------------------

class TestBulkFetchReturnsAllRequested:
    def test_fetch_three_of_five(self, conn):
        from propstore.relate import _bulk_get_claim_texts
        result = _bulk_get_claim_texts(conn, ["c1", "c3", "c5"])
        assert set(result.keys()) == {"c1", "c3", "c5"}

    def test_each_has_text_field(self, conn):
        from propstore.relate import _bulk_get_claim_texts
        result = _bulk_get_claim_texts(conn, ["c1", "c2", "c4", "c5"])
        for cid, d in result.items():
            assert "text" in d, f"claim {cid} missing 'text'"
            assert d["text"], f"claim {cid} has empty 'text'"


class TestBulkFetchMissingIdsSkipped:
    def test_nonexistent_ids_absent(self, conn):
        from propstore.relate import _bulk_get_claim_texts
        result = _bulk_get_claim_texts(conn, ["c1", "nonexistent", "c3"])
        assert "nonexistent" not in result
        assert set(result.keys()) == {"c1", "c3"}


class TestBulkFetchEmptyList:
    def test_empty_input_returns_empty(self, conn):
        from propstore.relate import _bulk_get_claim_texts
        result = _bulk_get_claim_texts(conn, [])
        assert result == {}


# ---------------------------------------------------------------------------
# Hypothesis: bulk fetch equivalence with per-claim fetch
# ---------------------------------------------------------------------------

class TestBulkFetchEquivalence:
    """_bulk_get_claim_texts returns identical data to per-claim _get_claim_text."""

    @pytest.mark.property
    @given(ids=st.lists(st.sampled_from(FIXTURE_IDS), min_size=0, max_size=5, unique=True))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_bulk_matches_individual(self, conn, ids):
        from propstore.relate import _bulk_get_claim_texts, _get_claim_text

        bulk = _bulk_get_claim_texts(conn, ids)
        individual = {}
        for cid in ids:
            d = _get_claim_text(conn, cid)
            if d is not None:
                individual[cid] = d

        assert bulk.keys() == individual.keys()
        for cid in bulk:
            # Compare the fields that matter
            for key in ("id", "text", "source_paper", "auto_summary", "statement", "expression"):
                assert bulk[cid].get(key) == individual[cid].get(key), (
                    f"Mismatch on {cid}.{key}: bulk={bulk[cid].get(key)!r} vs individual={individual[cid].get(key)!r}"
                )
