"""Calibration projection contract for the sidecar."""

from __future__ import annotations

from dataclasses import dataclass

from quire.projections import ProjectionColumn, ProjectionTable


CALIBRATION_COUNTS_PROJECTION = ProjectionTable(
    name="calibration_counts",
    columns=(
        ProjectionColumn("pass_number", "INTEGER", nullable=False),
        ProjectionColumn("category", "TEXT", nullable=False),
        ProjectionColumn("correct_count", "INTEGER", nullable=False),
        ProjectionColumn("total_count", "INTEGER", nullable=False),
    ),
    primary_key=("pass_number", "category"),
    if_not_exists=True,
)


@dataclass(frozen=True)
class CalibrationCountsProjectionRow:
    pass_number: int
    category: str
    correct_count: int
    total_count: int
