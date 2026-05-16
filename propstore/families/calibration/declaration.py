"""Calibration counts derived-store declaration and query helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from quire.projections import ProjectionTable, integer_field, text_field


CALIBRATION_COUNTS_PROJECTION = ProjectionTable(
    name="calibration_counts",
    columns=(
        integer_field("pass_number", nullable=False).column(),
        text_field("category", nullable=False).column(),
        integer_field("correct_count", nullable=False).column(),
        integer_field("total_count", nullable=False).column(),
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


def load_calibration_counts(
    conn: sqlite3.Connection,
) -> dict[tuple[int, str], tuple[int, int]] | None:
    """Load calibration validation data from the derived store."""

    try:
        rows = conn.execute(CALIBRATION_COUNTS_PROJECTION.select_all_sql()).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc).lower():
            raise
        return None
    if not rows:
        return None
    return {(row[0], row[1]): (row[2], row[3]) for row in rows}
