"""Opinion columns in the charter-derived ``stance`` projection (Phase 10-5).

The four subjective-logic components (Jøsang 2001, Def 9, p.7) ride on the
``stance`` table as nullable columns. Honest absence is the discipline: a stance
authored with no opinion leaves all four NULL, and the base rate carries no schema
default — a default base rate alone must never be promoted to "an opinion".

Page-image grounding:
papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from doxa import Opinion
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from quire.sqlalchemy_schema import SqlAlchemySchema
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.derived_schema import build_world_sidecar_schema

_OPINION_COLUMNS = (
    "opinion_belief",
    "opinion_disbelief",
    "opinion_uncertainty",
    "opinion_base_rate",
)


@st.composite
def valid_schema_opinions(draw: st.DrawFn) -> Opinion:
    u = draw(st.floats(min_value=0.0, max_value=1.0))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    assume(abs(b + d + u - 1.0) < 1e-9)
    return Opinion(b, d, u, a, allow_dogmatic=u < 1e-9)


def _write_stance(
    store: Path, schema: SqlAlchemySchema, values: dict[str, object]
) -> None:
    with writable_session(store, schema) as session:
        session.add_family("stance", values)
        session.commit()


def test_opinion_columns_exist() -> None:
    schema = build_world_sidecar_schema()
    columns = {column.name for column in schema.table("stance").columns}
    for name in _OPINION_COLUMNS:
        assert name in columns


def test_opinion_base_rate_has_no_schema_default() -> None:
    """The base-rate column carries no DDL default; absence stays absence."""

    schema = build_world_sidecar_schema()
    base_rate = schema.table("stance").columns["opinion_base_rate"]
    assert base_rate.nullable is True
    assert base_rate.server_default is None
    assert base_rate.default is None


def test_insert_with_opinion_values_roundtrips(tmp_path: Path) -> None:
    """An authored opinion round-trips through the ``stance`` projection."""

    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)
    _write_stance(
        store,
        schema,
        {
            "stance_id": "s1",
            "stance_type": "supports",
            "confidence": 0.8,
            "opinion_belief": 0.7,
            "opinion_disbelief": 0.1,
            "opinion_uncertainty": 0.2,
            "opinion_base_rate": 0.5,
        },
    )

    conn = sqlite3.connect(str(store))
    row = conn.execute(
        "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, "
        "opinion_base_rate FROM stance WHERE stance_id = 's1'"
    ).fetchone()
    assert row is not None
    assert abs(row[0] - 0.7) < 1e-9
    assert abs(row[1] - 0.1) < 1e-9
    assert abs(row[2] - 0.2) < 1e-9
    assert abs(row[3] - 0.5) < 1e-9


def test_insert_without_opinion_values_keeps_absence_explicit(tmp_path: Path) -> None:
    """A stance with no authored opinion leaves all four columns NULL."""

    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)
    _write_stance(
        store,
        schema,
        {"stance_id": "s1", "stance_type": "supports", "confidence": 0.9},
    )

    conn = sqlite3.connect(str(store))
    row = conn.execute(
        "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, "
        "opinion_base_rate FROM stance WHERE stance_id = 's1'"
    ).fetchone()
    assert row == (None, None, None, None)


def test_confidence_column_unaffected(tmp_path: Path) -> None:
    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)
    _write_stance(
        store,
        schema,
        {
            "stance_id": "s1",
            "stance_type": "supports",
            "confidence": 0.85,
            "opinion_belief": 0.6,
            "opinion_disbelief": 0.2,
            "opinion_uncertainty": 0.2,
            "opinion_base_rate": 0.5,
        },
    )

    conn = sqlite3.connect(str(store))
    row = conn.execute(
        "SELECT confidence FROM stance WHERE stance_id = 's1'"
    ).fetchone()
    assert row is not None
    assert abs(row[0] - 0.85) < 1e-9


@pytest.mark.property
@given(valid_schema_opinions())
@settings(deadline=None, max_examples=25)
def test_generated_opinion_tuple_roundtrips_as_opinion(
    tmp_path_factory: pytest.TempPathFactory, opinion: Opinion
) -> None:
    """Stored ``(b, d, u, a)`` reconstruct the same ``doxa.Opinion``."""

    schema = build_world_sidecar_schema()
    store = tmp_path_factory.mktemp("op") / "world.sqlite"
    create_sqlalchemy_store(store, schema)
    _write_stance(
        store,
        schema,
        {
            "stance_id": "s1",
            "stance_type": "supports",
            "confidence": opinion.expectation(),
            "opinion_belief": opinion.b,
            "opinion_disbelief": opinion.d,
            "opinion_uncertainty": opinion.u,
            "opinion_base_rate": opinion.a,
        },
    )

    conn = sqlite3.connect(str(store))
    row = conn.execute(
        "SELECT opinion_belief, opinion_disbelief, opinion_uncertainty, "
        "opinion_base_rate FROM stance WHERE stance_id = 's1'"
    ).fetchone()
    assert row is not None
    restored = Opinion(row[0], row[1], row[2], row[3], allow_dogmatic=row[2] < 1e-9)
    assert restored.b == pytest.approx(opinion.b, abs=1e-9)
    assert restored.d == pytest.approx(opinion.d, abs=1e-9)
    assert restored.u == pytest.approx(opinion.u, abs=1e-9)
    assert restored.a == pytest.approx(opinion.a, abs=1e-9)
