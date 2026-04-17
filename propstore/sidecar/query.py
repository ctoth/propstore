"""Read-only sidecar SQL queries."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from propstore.repository import Repository


class SidecarQueryError(Exception):
    pass


@dataclass(frozen=True)
class SidecarQueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def query_sidecar(repo: Repository, sql: str) -> SidecarQueryResult:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise FileNotFoundError(sidecar)

    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        raise SidecarQueryError(str(exc)) from exc
    finally:
        conn.close()

    if not rows:
        return SidecarQueryResult(columns=(), rows=())
    columns = tuple(rows[0].keys())
    return SidecarQueryResult(
        columns=columns,
        rows=tuple(tuple(str(row[column]) for column in columns) for row in rows),
    )
