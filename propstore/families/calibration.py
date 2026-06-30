"""Calibration-counts projection charter.

A validation set of human-judged stances yields, per ``(pass_number, category)``
pair, how many model labels were correct out of how many total. Those counts are
the empirical evidence that turns a categorical model label into an informative
``doxa.Opinion`` (see :func:`propstore.heuristic.calibrate.categorical_to_opinion`,
which accepts a ``calibration_counts`` mapping). This charter is the sidecar
projection that carries those counts: one row per ``(pass_number, category)`` pair.

``CalibrationCount`` is a derived-only projection family (never authored to git):
it carries no ``semantic`` tag and declares no foreign keys, mirroring
:class:`~propstore.families.diagnostics.BuildDiagnostic`. The counts are
calibration evidence about model behaviour, not claims about the world, so a hard
referential constraint would be meaningless.

The reader :func:`load_calibration_counts` lowers the projected rows back into the
``dict[(pass_number, category), (correct_count, total_count)]`` shape that
``categorical_to_opinion`` consumes — the one place the projection round-trips.
"""

from __future__ import annotations

import sqlite3
from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field


@charter(
    key="calibration_counts",
    name="calibration_counts",
    contract_version="2026.06.29",
    placement="calibration_counts",
    identity_field="calibration_id",
)
class CalibrationCount(CharterDoc):
    """One ``(pass_number, category)`` calibration tally.

    ``correct_count`` is how many model labels in this bucket matched the
    human judgement; ``total_count`` is the bucket size. ``calibration_id`` is the
    synthetic ``"{pass_number}:{category}"`` identity that makes the pair unique.
    """

    calibration_id: Annotated[str, charter_field(primary_key=True)]
    pass_number: int
    category: str
    correct_count: int
    total_count: int


def calibration_count_id(pass_number: int, category: str) -> str:
    """The synthetic identity for a ``(pass_number, category)`` calibration row."""

    return f"{pass_number}:{category}"


def load_calibration_counts(
    conn: sqlite3.Connection,
) -> dict[tuple[int, str], tuple[int, int]]:
    """Read the calibration-counts projection into the categorical-mapping shape.

    Returns the ``dict[(pass_number, category), (correct_count, total_count)]``
    that :func:`propstore.heuristic.calibrate.categorical_to_opinion` consumes.
    """

    rows = conn.execute(
        'SELECT "pass_number", "category", "correct_count", "total_count" '
        'FROM "calibration_counts"'
    ).fetchall()
    return {
        (int(pass_number), str(category)): (int(correct_count), int(total_count))
        for pass_number, category, correct_count, total_count in rows
    }
