from __future__ import annotations

import sqlite3

from propstore.heuristic.calibrate import load_calibration_counts
from propstore.sidecar.calibration import CALIBRATION_COUNTS_PROJECTION


def test_calibration_counts_uses_generated_ddl_and_reader_sql() -> None:
    assert CALIBRATION_COUNTS_PROJECTION.insert_sql() == (
        'INSERT INTO "calibration_counts" '
        '("pass_number", "category", "correct_count", "total_count") '
        "VALUES (:pass_number, :category, :correct_count, :total_count)"
    )
    assert CALIBRATION_COUNTS_PROJECTION.select_all_sql() == (
        'SELECT "pass_number", "category", "correct_count", "total_count" '
        'FROM "calibration_counts"'
    )

    conn = sqlite3.connect(":memory:")
    for statement in CALIBRATION_COUNTS_PROJECTION.ddl_statements():
        conn.execute(statement)
    conn.execute(
        CALIBRATION_COUNTS_PROJECTION.insert_sql(),
        {
            "pass_number": 1,
            "category": "strong",
            "correct_count": 80,
            "total_count": 100,
        },
    )

    assert load_calibration_counts(conn) == {(1, "strong"): (80, 100)}
