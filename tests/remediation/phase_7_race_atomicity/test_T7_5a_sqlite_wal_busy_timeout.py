from __future__ import annotations

import sqlite3
import threading
import time

from propstore.sidecar.sqlite import SIDECAR_BUSY_TIMEOUT_MS, connect_sidecar


def test_sidecar_connect_enables_wal_and_busy_timeout(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"

    with connect_sidecar(sidecar_path) as conn:
        conn.execute("CREATE TABLE item (id INTEGER PRIMARY KEY)")
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]

    assert str(journal_mode).lower() == "wal"
    assert int(busy_timeout) >= SIDECAR_BUSY_TIMEOUT_MS


def test_concurrent_sqlite_writer_waits_for_busy_timeout(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    with connect_sidecar(sidecar_path) as conn:
        conn.execute("CREATE TABLE item (id INTEGER PRIMARY KEY)")
        conn.commit()

    blocker = connect_sidecar(sidecar_path)
    blocker.execute("BEGIN IMMEDIATE")
    blocker.execute("INSERT INTO item (id) VALUES (1)")

    errors: list[str] = []
    started = threading.Event()

    def write_waiting() -> None:
        started.set()
        try:
            with connect_sidecar(sidecar_path) as conn:
                conn.execute("INSERT INTO item (id) VALUES (2)")
                conn.commit()
        except sqlite3.OperationalError as exc:
            errors.append(str(exc))

    writer = threading.Thread(target=write_waiting)
    writer.start()
    assert started.wait(timeout=1.0)
    time.sleep(0.05)
    assert writer.is_alive()

    blocker.commit()
    blocker.close()
    writer.join(timeout=SIDECAR_BUSY_TIMEOUT_MS / 1000)

    assert errors == []
    with connect_sidecar(sidecar_path) as conn:
        rows = conn.execute("SELECT id FROM item ORDER BY id").fetchall()
    assert [row[0] for row in rows] == [1, 2]
