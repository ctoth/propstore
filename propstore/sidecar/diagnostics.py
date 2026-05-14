"""Build-diagnostics projection contract for the sidecar."""

from __future__ import annotations

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
