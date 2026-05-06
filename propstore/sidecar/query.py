"""Read-only sidecar SQL queries."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from propstore.reporting import JsonReportMixin
from propstore.repository import Repository
from propstore.sidecar.sqlite import connect_sidecar_readonly


class SidecarQueryError(Exception):
    pass


@dataclass(frozen=True)
class SidecarQueryResult(JsonReportMixin):
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def query_sidecar(repo: Repository, sql: str) -> SidecarQueryResult:
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        raise FileNotFoundError(sidecar)

    conn = connect_sidecar_readonly(sidecar)
    conn.row_factory = sqlite3.Row
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
