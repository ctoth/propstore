"""Tests for opinion columns in claim_stance schema.

Verifies that the four subjective logic opinion columns
(Josang 2001, Def 9, p.7) are present and functional in claim_stance.

Page-image grounding:
papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
"""

import sqlite3
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.opinion import Opinion
from propstore.sidecar.schema import create_tables
from tests.conftest import create_argumentation_schema, insert_claim, insert_stance


@pytest.fixture
def conn():
    """In-memory SQLite with schema."""
    c = sqlite3.connect(":memory:")
    create_argumentation_schema(c)
    return c


def _insert_claims(conn):
    """Insert two claims for FK targets."""
    insert_claim(conn, "c1", claim_type="parameter", concept_id="concept1", value=1.0, source_paper="paper1")
    insert_claim(conn, "c2", claim_type="parameter", concept_id="concept1", value=2.0, source_paper="paper1")


@st.composite
def valid_schema_opinions(draw):
    """Generate valid opinion tuples for storage roundtrip behavior."""
    u = draw(st.floats(min_value=0.0, max_value=1.0))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    assume(abs(b + d + u - 1.0) < 1e-9)
    return Opinion(b, d, u, a)


class TestOpinionSchemaColumns:
    """Test that claim_stance table has the opinion columns after schema creation."""

    def test_opinion_columns_exist(self, conn):
        """claim_stance must have opinion_belief, opinion_disbelief,
        opinion_uncertainty, opinion_base_rate columns."""
        cur = conn.execute("PRAGMA table_info(relation_edge)")
        columns = {row[1] for row in cur.fetchall()}
        assert "opinion_belief" in columns
        assert "opinion_disbelief" in columns
        assert "opinion_uncertainty" in columns
        assert "opinion_base_rate" in columns

    def test_opinion_base_rate_has_no_schema_default(self, conn):
        cur = conn.execute("PRAGMA table_info(relation_edge)")
        defaults = {row[1]: row[4] for row in cur.fetchall()}

        assert defaults["opinion_base_rate"] is None

    def test_sidecar_opinion_base_rate_has_no_schema_default(self):
        sidecar = sqlite3.connect(":memory:")
        create_tables(sidecar)
        cur = sidecar.execute("PRAGMA table_info(relation_edge)")
        defaults = {row[1]: row[4] for row in cur.fetchall()}

        assert defaults["opinion_base_rate"] is None

    def test_insert_with_opinion_values_roundtrips(self, conn):
        """INSERT with explicit opinion values should round-trip via SELECT.

        Jøsang's opinion tuple is (belief, disbelief, uncertainty,
        base-rate):
        papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
        """
        _insert_claims(conn)

        # Insert stance with opinion values: b=0.7, d=0.1, u=0.2, a=0.5
        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.8, opinion_belief=0.7, opinion_disbelief=0.1,
            opinion_uncertainty=0.2, opinion_base_rate=0.5,
        )

        row = conn.execute(
            "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate "
            "FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert abs(row[0] - 0.7) < 1e-9
        assert abs(row[1] - 0.1) < 1e-9
        assert abs(row[2] - 0.2) < 1e-9
        assert abs(row[3] - 0.5) < 1e-9

    @pytest.mark.property
    @given(valid_schema_opinions())
    @settings(deadline=None)
    def test_generated_opinion_tuple_roundtrips_as_opinion(self, opinion):
        """Generated opinion fields roundtrip through storage as an Opinion.

        This guards the behavior, not just the presence of nullable columns:
        b, d, u, and a remain the subjective-logic tuple described by
        Jøsang 2001 Definition 9.

        papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
        """
        conn = sqlite3.connect(":memory:")
        create_argumentation_schema(conn)
        _insert_claims(conn)
        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=opinion.expectation(),
            opinion_belief=opinion.b,
            opinion_disbelief=opinion.d,
            opinion_uncertainty=opinion.u,
            opinion_base_rate=opinion.a,
        )

        row = conn.execute(
            "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate "
            "FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row is not None
        restored = Opinion(row[0], row[1], row[2], row[3])
        assert restored.b == pytest.approx(opinion.b, abs=1e-9)
        assert restored.d == pytest.approx(opinion.d, abs=1e-9)
        assert restored.u == pytest.approx(opinion.u, abs=1e-9)
        assert restored.a == pytest.approx(opinion.a, abs=1e-9)

    def test_insert_without_opinion_values_backward_compat(self, conn):
        """Missing opinion evidence remains explicit at the storage boundary.

        Belief, disbelief, and uncertainty remain NULL when no opinion was
        authored. The base-rate default alone is not treated as an opinion.
        """
        _insert_claims(conn)

        # Insert stance WITHOUT opinion values — backward compat
        insert_stance(conn, "c1", "c2", "supports", confidence=0.9)

        row = conn.execute(
            "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate "
            "FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert row[0] is None  # opinion_belief NULL
        assert row[1] is None  # opinion_disbelief NULL
        assert row[2] is None  # opinion_uncertainty NULL
        assert row[3] is None  # opinion_base_rate NULL

    def test_confidence_column_unaffected(self, conn):
        """Existing confidence column must be completely unaffected by new columns."""
        _insert_claims(conn)

        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.85, opinion_belief=0.6, opinion_disbelief=0.2,
            opinion_uncertainty=0.2, opinion_base_rate=0.5,
        )

        row = conn.execute(
            "SELECT confidence FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert abs(row[0] - 0.85) < 1e-9

    def test_select_star_returns_opinion_columns(self, conn):
        """SELECT * must include opinion columns in result dicts."""
        _insert_claims(conn)

        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.8, opinion_belief=0.7, opinion_disbelief=0.1,
            opinion_uncertainty=0.2, opinion_base_rate=0.5,
        )

        # Use row_factory to get dict-like access
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row["opinion_belief"] is not None
        assert abs(row["opinion_belief"] - 0.7) < 1e-9
        assert abs(row["opinion_disbelief"] - 0.1) < 1e-9
        assert abs(row["opinion_uncertainty"] - 0.2) < 1e-9
        assert abs(row["opinion_base_rate"] - 0.5) < 1e-9
