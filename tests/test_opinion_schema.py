"""Tests for opinion columns in claim_stance schema.

Verifies that the four subjective logic opinion columns
(Josang 2001, Def 9, p.7) are present and functional in claim_stance.
"""

import sqlite3
import pytest

from tests.conftest import create_argumentation_schema


@pytest.fixture
def conn():
    """In-memory SQLite with schema."""
    c = sqlite3.connect(":memory:")
    create_argumentation_schema(c)
    return c


def _insert_claims(conn):
    """Insert two claims for FK targets."""
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, source_paper, provenance_page) "
        "VALUES ('c1', 'parameter', 'concept1', 1.0, 'paper1', 1)"
    )
    conn.execute(
        "INSERT INTO claim (id, type, concept_id, value, source_paper, provenance_page) "
        "VALUES ('c2', 'parameter', 'concept1', 2.0, 'paper1', 1)"
    )


class TestOpinionSchemaColumns:
    """Test that claim_stance table has the opinion columns after schema creation."""

    def test_opinion_columns_exist(self, conn):
        """claim_stance must have opinion_belief, opinion_disbelief,
        opinion_uncertainty, opinion_base_rate columns."""
        cur = conn.execute("PRAGMA table_info(claim_stance)")
        columns = {row[1] for row in cur.fetchall()}
        assert "opinion_belief" in columns
        assert "opinion_disbelief" in columns
        assert "opinion_uncertainty" in columns
        assert "opinion_base_rate" in columns

    def test_insert_with_opinion_values_roundtrips(self, conn):
        """INSERT with explicit opinion values should round-trip via SELECT."""
        _insert_claims(conn)

        # Insert stance with opinion values: b=0.7, d=0.1, u=0.2, a=0.5
        conn.execute(
            "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence, "
            "opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("c1", "c2", "supports", 0.8, 0.7, 0.1, 0.2, 0.5),
        )

        row = conn.execute(
            "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate "
            "FROM claim_stance WHERE claim_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert abs(row[0] - 0.7) < 1e-9
        assert abs(row[1] - 0.1) < 1e-9
        assert abs(row[2] - 0.2) < 1e-9
        assert abs(row[3] - 0.5) < 1e-9

    def test_insert_without_opinion_values_backward_compat(self, conn):
        """INSERT without opinion values should work — columns default to NULL
        (except opinion_base_rate which defaults to 0.5)."""
        _insert_claims(conn)

        # Insert stance WITHOUT opinion values — backward compat
        conn.execute(
            "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "c2", "supports", 0.9),
        )

        row = conn.execute(
            "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate "
            "FROM claim_stance WHERE claim_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert row[0] is None  # opinion_belief NULL
        assert row[1] is None  # opinion_disbelief NULL
        assert row[2] is None  # opinion_uncertainty NULL
        assert abs(row[3] - 0.5) < 1e-9  # opinion_base_rate defaults to 0.5

    def test_confidence_column_unaffected(self, conn):
        """Existing confidence column must be completely unaffected by new columns."""
        _insert_claims(conn)

        conn.execute(
            "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence, "
            "opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("c1", "c2", "supports", 0.85, 0.6, 0.2, 0.2, 0.5),
        )

        row = conn.execute(
            "SELECT confidence FROM claim_stance WHERE claim_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert abs(row[0] - 0.85) < 1e-9

    def test_select_star_returns_opinion_columns(self, conn):
        """SELECT * must include opinion columns in result dicts."""
        _insert_claims(conn)

        conn.execute(
            "INSERT INTO claim_stance (claim_id, target_claim_id, stance_type, confidence, "
            "opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("c1", "c2", "supports", 0.8, 0.7, 0.1, 0.2, 0.5),
        )

        # Use row_factory to get dict-like access
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM claim_stance WHERE claim_id = 'c1'"
        ).fetchone()

        assert row["opinion_belief"] is not None
        assert abs(row["opinion_belief"] - 0.7) < 1e-9
        assert abs(row["opinion_disbelief"] - 0.1) < 1e-9
        assert abs(row["opinion_uncertainty"] - 0.2) < 1e-9
        assert abs(row["opinion_base_rate"] - 0.5) < 1e-9
