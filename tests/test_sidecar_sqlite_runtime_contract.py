from __future__ import annotations

import sqlite3
from contextlib import closing

from propstore.sidecar.sqlite import connect_sidecar, connect_sidecar_readonly


def _sqlite_artifacts(path):
    return (
        path,
        path.with_name(f"{path.name}-wal"),
        path.with_name(f"{path.name}-shm"),
    )


def _checkpoint_and_close(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()


def test_readonly_connection_to_wal_database_creates_runtime_wal_or_shm(tmp_path) -> None:
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    conn.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO item (id, value) VALUES (1, 'alpha')")
    conn.commit()
    _checkpoint_and_close(conn)

    for artifact in _sqlite_artifacts(sidecar_path)[1:]:
        assert not artifact.exists()

    with closing(connect_sidecar_readonly(sidecar_path)) as readonly:
        row = readonly.execute("SELECT value FROM item WHERE id = 1").fetchone()

    assert row[0] == "alpha"
    assert any(artifact.exists() for artifact in _sqlite_artifacts(sidecar_path)[1:])


def test_checkpointed_sqlite_file_can_publish_without_wal_or_shm_siblings(tmp_path) -> None:
    final_path = tmp_path / "published.sqlite"
    temp_path = tmp_path / ".published.sqlite.tmp"

    conn = connect_sidecar(temp_path)
    conn.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO item (id, value) VALUES (1, 'published')")
    conn.commit()
    _checkpoint_and_close(conn)

    temp_path.replace(final_path)

    assert final_path.exists()
    assert not temp_path.exists()
    for artifact in _sqlite_artifacts(temp_path)[1:]:
        assert not artifact.exists()
    for artifact in _sqlite_artifacts(final_path)[1:]:
        assert not artifact.exists()

    with sqlite3.connect(final_path) as conn:
        row = conn.execute("SELECT value FROM item WHERE id = 1").fetchone()

    assert row[0] == "published"
