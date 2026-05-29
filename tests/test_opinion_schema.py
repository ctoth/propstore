"""Tests for the relation-edge opinion column in the argumentation schema.

The relation-opinion storage holds the subjective-logic opinion
(Josang 2001, Def 9, p.7) as a single typed ``opinion`` column carrying the
serialized ``Opinion`` (msgspec JSON ``{"b","d","u","a","allow_dogmatic"}``),
not four scalar ``opinion_belief/_disbelief/_uncertainty/_base_rate`` columns.
These tests verify the column shape and round-trip behavior.

Page-image grounding:
papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
"""

import sqlite3

import msgspec
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from propstore.opinion import Opinion
from tests.conftest import create_argumentation_schema, insert_claim, insert_stance
from tests.sidecar_schema_helpers import build_world_projection_schema

_DROPPED_SCALAR_COLUMNS = (
    "opinion_belief",
    "opinion_disbelief",
    "opinion_uncertainty",
    "opinion_base_rate",
)


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


def _select_opinion(conn) -> Opinion | None:
    """Read the relation-edge ``opinion`` column for c1 and decode it."""
    row = conn.execute(
        "SELECT opinion FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
    ).fetchone()
    assert row is not None
    if row[0] is None:
        return None
    return msgspec.json.decode(row[0], type=Opinion)


@st.composite
def valid_schema_opinions(draw):
    """Generate valid opinion tuples for storage roundtrip behavior."""
    u = draw(st.floats(min_value=0.0, max_value=1.0))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    assume(abs(b + d + u - 1.0) < 1e-9)
    return Opinion(b, d, u, a, allow_dogmatic=u < 1e-9)


class TestOpinionSchemaColumn:
    """The relation_edge table carries a single typed ``opinion`` column."""

    def test_opinion_column_exists(self, conn):
        """relation_edge must have a single ``opinion`` column and none of the
        four dropped scalar columns."""
        cur = conn.execute("PRAGMA table_info(relation_edge)")
        columns = {row[1] for row in cur.fetchall()}
        assert "opinion" in columns
        for scalar in _DROPPED_SCALAR_COLUMNS:
            assert scalar not in columns

    def test_opinion_column_has_no_schema_default(self, conn):
        cur = conn.execute("PRAGMA table_info(relation_edge)")
        defaults = {row[1]: row[4] for row in cur.fetchall()}

        assert defaults["opinion"] is None

    def test_sidecar_opinion_column_has_no_schema_default(self):
        sidecar = sqlite3.connect(":memory:")
        build_world_projection_schema(sidecar)
        cur = sidecar.execute("PRAGMA table_info(relation_edge)")
        columns = {row[1]: row[4] for row in cur.fetchall()}

        assert "opinion" in columns
        for scalar in _DROPPED_SCALAR_COLUMNS:
            assert scalar not in columns
        assert columns["opinion"] is None

    def test_insert_with_opinion_value_roundtrips(self, conn):
        """INSERT with an explicit opinion should round-trip via SELECT.

        Jøsang's opinion tuple is (belief, disbelief, uncertainty,
        base-rate):
        papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
        """
        _insert_claims(conn)

        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.8, opinion=Opinion(0.7, 0.1, 0.2, 0.5),
        )

        restored = _select_opinion(conn)
        assert restored is not None
        assert restored.b == pytest.approx(0.7, abs=1e-9)
        assert restored.d == pytest.approx(0.1, abs=1e-9)
        assert restored.u == pytest.approx(0.2, abs=1e-9)
        assert restored.a == pytest.approx(0.5, abs=1e-9)

    @pytest.mark.property
    @given(valid_schema_opinions())
    @settings(deadline=None)
    def test_generated_opinion_tuple_roundtrips_as_opinion(self, opinion):
        """A generated opinion roundtrips through storage as an Opinion.

        This guards the behavior, not just column presence: b, d, u, and a
        remain the subjective-logic tuple described by Jøsang 2001
        Definition 9.

        papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
        """
        conn = sqlite3.connect(":memory:")
        create_argumentation_schema(conn)
        _insert_claims(conn)
        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=opinion.expectation(),
            opinion=opinion,
        )

        restored = _select_opinion(conn)
        assert restored is not None
        assert restored.b == pytest.approx(opinion.b, abs=1e-9)
        assert restored.d == pytest.approx(opinion.d, abs=1e-9)
        assert restored.u == pytest.approx(opinion.u, abs=1e-9)
        assert restored.a == pytest.approx(opinion.a, abs=1e-9)

    def test_insert_without_opinion_value_is_null(self, conn):
        """Missing opinion evidence remains explicit at the storage boundary.

        The opinion column is NULL when no opinion was authored.
        """
        _insert_claims(conn)

        insert_stance(conn, "c1", "c2", "supports", confidence=0.9)

        assert _select_opinion(conn) is None

    def test_confidence_column_unaffected(self, conn):
        """The confidence column is unaffected by the opinion column."""
        _insert_claims(conn)

        insert_stance(
            conn, "c1", "c2", "supports",
            confidence=0.85, opinion=Opinion(0.6, 0.2, 0.2, 0.5),
        )

        row = conn.execute(
            "SELECT confidence FROM relation_edge WHERE source_kind='claim' AND source_id = 'c1'"
        ).fetchone()

        assert row is not None
        assert abs(row[0] - 0.85) < 1e-9
