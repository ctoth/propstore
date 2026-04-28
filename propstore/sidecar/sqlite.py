from __future__ import annotations

import sqlite3
from os import PathLike
from pathlib import Path

SIDECAR_BUSY_TIMEOUT_MS = 30_000


def connect_sidecar(path: str | PathLike[str]) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    try:
        configure_sidecar_connection(conn)
    except Exception:
        conn.close()
        raise
    return conn


def connect_sidecar_readonly(path: str | PathLike[str]) -> sqlite3.Connection:
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute(f"PRAGMA busy_timeout = {SIDECAR_BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA query_only = ON")
    except Exception:
        conn.close()
        raise
    return conn


def configure_sidecar_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.execute(f"PRAGMA busy_timeout = {SIDECAR_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
