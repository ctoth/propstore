"""Calibration count typed query contract."""

from __future__ import annotations

from sqlalchemy import select

from quire.charters import FamilyModel
from quire.sqlalchemy_store import DerivedSession


class CalibrationCount(FamilyModel):
    pass


def calibration_counts_by_key(
    derived: DerivedSession,
) -> dict[tuple[int, str], tuple[int, int]] | None:
    """Return calibration evidence keyed by pass number and category."""

    rows = derived.session.execute(select(CalibrationCount)).scalars()
    counts: dict[tuple[int, str], tuple[int, int]] = {}
    for row in rows:
        counts[
            (int(getattr(row, "pass_number")), str(getattr(row, "category")))
        ] = (
            int(getattr(row, "correct_count")),
            int(getattr(row, "total_count")),
        )
    return counts or None
