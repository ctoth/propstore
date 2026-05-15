"""Build-diagnostics projection and query contract."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from quire.projections import ProjectionColumn, ProjectionIndex, ProjectionTable


BUILD_DIAGNOSTICS_PROJECTION = ProjectionTable(
    name="build_diagnostics",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("claim_id", "TEXT"),
        ProjectionColumn("source_kind", "TEXT", nullable=False),
        ProjectionColumn("source_ref", "TEXT"),
        ProjectionColumn("diagnostic_kind", "TEXT", nullable=False),
        ProjectionColumn("severity", "TEXT", nullable=False),
        ProjectionColumn("blocking", "INTEGER", nullable=False),
        ProjectionColumn("message", "TEXT", nullable=False),
        ProjectionColumn("file", "TEXT"),
        ProjectionColumn("detail_json", "TEXT"),
    ),
    indexes=(
        ProjectionIndex("idx_build_diagnostics_claim", ("claim_id",)),
        ProjectionIndex("idx_build_diagnostics_kind", ("diagnostic_kind",)),
        ProjectionIndex(
            "idx_build_diagnostics_source",
            ("source_kind", "source_ref"),
        ),
    ),
    if_not_exists=True,
)


@dataclass(frozen=True, slots=True)
class Written:
    artifact_id: str
    kind: str


@dataclass(frozen=True, slots=True)
class Quarantined:
    artifact_id: str
    kind: str
    diagnostic_id: int
    message: str


@dataclass(frozen=True, slots=True)
class SourceStatusDiagnosticRow:
    claim_id: str | None
    source_ref: str | None
    diagnostic_kind: str
    message: str


class QuarantinableWriter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        for statement in BUILD_DIAGNOSTICS_PROJECTION.ddl_statements():
            conn.execute(statement)

    def try_write(
        self,
        *,
        artifact_id: str,
        kind: str,
        payload: object,
        write: Callable[[object], None] | None = None,
        diagnostic_kind: str | None = None,
        file: str | None = None,
    ) -> Written | Quarantined:
        """Write a payload or quarantine its failure as a diagnostic row."""
        try:
            if payload is None:
                raise ValueError("payload is None")
            if write is not None:
                write(payload)
        except Exception as exc:
            return self._quarantine(
                artifact_id=artifact_id,
                kind=kind,
                diagnostic_kind=diagnostic_kind or f"{kind}_quarantine",
                message=str(exc) or exc.__class__.__name__,
                file=file,
            )
        return Written(artifact_id=artifact_id, kind=kind)

    def quarantine(
        self,
        *,
        artifact_id: str,
        kind: str,
        diagnostic_kind: str,
        message: str,
        file: str | None = None,
    ) -> Quarantined:
        return self._quarantine(
            artifact_id=artifact_id,
            kind=kind,
            diagnostic_kind=diagnostic_kind,
            message=message,
            file=file,
        )

    def _quarantine(
        self,
        *,
        artifact_id: str,
        kind: str,
        diagnostic_kind: str,
        message: str,
        file: str | None,
    ) -> Quarantined:
        detail_json = json.dumps(
            {
                "artifact_id": artifact_id,
                "kind": kind,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        row = BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=artifact_id if kind == "claim" else None,
            source_kind=kind,
            source_ref=artifact_id,
            diagnostic_kind=diagnostic_kind,
            severity="error",
            blocking=1,
            message=message,
            file=file,
            detail_json=detail_json,
        )
        cursor = self._conn.execute(
            BUILD_DIAGNOSTICS_PROJECTION.insert_sql(),
            BUILD_DIAGNOSTICS_PROJECTION.encode_row(row),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("build_diagnostics insert did not return a row id")
        return Quarantined(
            artifact_id=artifact_id,
            kind=kind,
            diagnostic_id=cursor.lastrowid,
            message=message,
        )


def has_build_diagnostics_table(conn: sqlite3.Connection) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='build_diagnostics'"
        ).fetchone()
        is not None
    )


def select_build_diagnostics(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            id, claim_id, source_kind, source_ref,
            diagnostic_kind, severity, blocking,
            message, file, detail_json
        FROM build_diagnostics
        ORDER BY id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def select_source_status_diagnostic_rows(
    conn: sqlite3.Connection,
    *,
    claim_ids: Sequence[str],
    like_pattern: str,
) -> list[SourceStatusDiagnosticRow]:
    if not claim_ids:
        return []
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT claim_id, source_ref, diagnostic_kind, message
        FROM build_diagnostics
        WHERE source_kind = 'claim'
          AND (claim_id IN ({placeholders}) OR source_ref LIKE ? ESCAPE '!')
        ORDER BY id
        """,
        (*claim_ids, like_pattern),
    ).fetchall()
    return [
        SourceStatusDiagnosticRow(
            claim_id=None if row[0] is None else str(row[0]),
            source_ref=None if row[1] is None else str(row[1]),
            diagnostic_kind=str(row[2]),
            message=str(row[3]),
        )
        for row in rows
    ]


def delete_promotion_blocked_diagnostics(
    conn: sqlite3.Connection,
    claim_id: str,
) -> None:
    conn.execute(
        "DELETE FROM build_diagnostics "
        "WHERE claim_id = ? AND diagnostic_kind = 'promotion_blocked'",
        (claim_id,),
    )
