from __future__ import annotations

import sqlite3
import struct
from contextlib import closing

import pytest

from propstore.heuristic.embed import _load_vec_extension


def _load_or_skip(conn: sqlite3.Connection) -> None:
    try:
        _load_vec_extension(conn)
    except ImportError as exc:
        pytest.skip(str(exc))
    except sqlite3.OperationalError as exc:
        pytest.skip(f"sqlite-vec could not load in this environment: {exc}")


def _vector_blob(left: float, right: float) -> bytes:
    return struct.pack("2f", left, right)


def test_sqlite_vec_virtual_table_can_be_created_in_memory() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        _load_or_skip(conn)
        conn.execute("CREATE VIRTUAL TABLE claim_vec_model USING vec0(embedding float[2])")
        conn.execute(
            "INSERT INTO claim_vec_model(rowid, embedding) VALUES (?, ?)",
            (7, _vector_blob(0.25, 0.75)),
        )
        row = conn.execute(
            "SELECT rowid, embedding FROM claim_vec_model WHERE rowid = ?",
            (7,),
        ).fetchone()

    assert row[0] == 7
    assert bytes(row[1]) == _vector_blob(0.25, 0.75)


def test_sqlite_vec_rows_can_restore_from_separate_cache_database(tmp_path) -> None:
    cache_path = tmp_path / "embedding-cache.sqlite"
    sidecar_path = tmp_path / "world-sidecar.sqlite"
    vector = _vector_blob(0.5, 0.125)

    with closing(sqlite3.connect(cache_path)) as cache:
        _load_or_skip(cache)
        cache.execute("CREATE VIRTUAL TABLE claim_vec_model USING vec0(embedding float[2])")
        cache.execute(
            "INSERT INTO claim_vec_model(rowid, embedding) VALUES (?, ?)",
            (11, vector),
        )
        cache.commit()

    with closing(sqlite3.connect(cache_path)) as cache:
        _load_or_skip(cache)
        rows = cache.execute(
            "SELECT rowid, embedding FROM claim_vec_model ORDER BY rowid"
        ).fetchall()

    with closing(sqlite3.connect(sidecar_path)) as sidecar:
        _load_or_skip(sidecar)
        sidecar.execute("CREATE VIRTUAL TABLE claim_vec_model USING vec0(embedding float[2])")
        sidecar.executemany(
            "INSERT INTO claim_vec_model(rowid, embedding) VALUES (?, ?)",
            [(int(row[0]), bytes(row[1])) for row in rows],
        )
        sidecar.commit()
        restored = sidecar.execute(
            "SELECT rowid, embedding FROM claim_vec_model WHERE rowid = ?",
            (11,),
        ).fetchone()

    assert restored[0] == 11
    assert bytes(restored[1]) == vector
