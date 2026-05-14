from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from quire.projections import FtsProjection
from propstore.sidecar.sqlite import connect_sidecar, connect_sidecar_readonly


def _skip_if_fts5_unavailable() -> None:
    try:
        with sqlite3.connect(":memory:") as conn:
            conn.execute("CREATE VIRTUAL TABLE probe_fts USING fts5(value)")
    except sqlite3.OperationalError as exc:
        pytest.skip(f"SQLite FTS5 is unavailable: {exc}")


def test_fts5_table_is_queryable_from_readonly_sidecar_connection(tmp_path) -> None:
    _skip_if_fts5_unavailable()
    sidecar_path = tmp_path / "propstore.sqlite"
    projection = FtsProjection(
        table="concept_fts",
        key_column="concept_id",
        columns=("canonical_name", "aliases", "definition", "conditions"),
        row_plan="test rows",
    )
    with closing(connect_sidecar(sidecar_path)) as conn:
        conn.execute(projection.ddl_statements()[0])
        conn.execute(
            projection.insert_sql(),
            {
                "concept_id": "ps:concept:frequency",
                "canonical_name": "fundamental frequency",
                "aliases": "pitch f0",
                "definition": "A periodic acoustic feature",
                "conditions": "task == 'speech'",
            },
        )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    with closing(connect_sidecar_readonly(sidecar_path)) as readonly:
        rows = readonly.execute(
            projection.match_sql(("concept_id",)),
            {"query": "pitch"},
        ).fetchall()

    assert [row[0] for row in rows] == ["ps:concept:frequency"]


def test_fts5_virtual_table_creation_requires_writable_connection(tmp_path) -> None:
    _skip_if_fts5_unavailable()
    sidecar_path = tmp_path / "propstore.sqlite"
    with sqlite3.connect(sidecar_path) as conn:
        conn.execute("CREATE TABLE marker (id INTEGER PRIMARY KEY)")

    with closing(connect_sidecar_readonly(sidecar_path)) as readonly:
        with pytest.raises(sqlite3.OperationalError):
            readonly.execute("CREATE VIRTUAL TABLE claim_fts USING fts5(statement)")
