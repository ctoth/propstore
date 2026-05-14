"""Build-diagnostics projection contract for the sidecar."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass

from propstore.sidecar.projection import ProjectionColumn, ProjectionIndex, ProjectionTable


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


@dataclass(frozen=True)
class BuildDiagnosticProjectionRow:
    claim_id: object
    source_kind: object
    source_ref: object
    diagnostic_kind: object
    severity: object
    blocking: object
    message: object
    file: object
    detail_json: object

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "BuildDiagnosticProjectionRow":
        return cls(*values)

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "claim_id": self.claim_id,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "diagnostic_kind": self.diagnostic_kind,
            "severity": self.severity,
            "blocking": self.blocking,
            "message": self.message,
            "file": self.file,
            "detail_json": self.detail_json,
        }


def create_build_diagnostics_table(conn: sqlite3.Connection) -> None:
    for statement in BUILD_DIAGNOSTICS_PROJECTION.ddl_statements():
        conn.execute(statement)


def insert_build_diagnostic(
    conn: sqlite3.Connection,
    row: BuildDiagnosticProjectionRow,
) -> sqlite3.Cursor:
    return conn.execute(
        BUILD_DIAGNOSTICS_PROJECTION.insert_sql(),
        row.as_insert_mapping(),
    )
