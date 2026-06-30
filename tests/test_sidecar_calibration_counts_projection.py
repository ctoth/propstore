"""Calibration-counts sidecar projection (Phase 10-5, deferred row A5).

The validation-set tallies that turn a categorical model label into an
informative ``doxa.Opinion`` project into the charter-derived world sidecar as the
``calibration_counts`` table — the projection IS the
:class:`propstore.families.calibration.CalibrationCount` charter, populated by
``session.add_family`` like every other derived-only family. The reader
:func:`propstore.families.calibration.load_calibration_counts` lowers the rows
back into the ``dict[(pass_number, category), (correct, total)]`` shape that
:func:`propstore.heuristic.calibrate.categorical_to_opinion` consumes, closing the
calibration loop.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from doxa import Opinion
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.derived_schema import build_world_sidecar_schema
from propstore.families.calibration import (
    calibration_count_id,
    load_calibration_counts,
)
from propstore.heuristic.calibrate import (
    CalibrationSource,
    CategoryPrior,
    categorical_to_opinion,
)
from propstore.provenance import Provenance, ProvenanceStatus


def _category_prior(category: str, value: float = 0.5) -> CategoryPrior:
    return CategoryPrior(
        category=category,
        value=value,
        source=CalibrationSource.MEASURED,
        provenance=Provenance(
            status=ProvenanceStatus.CALIBRATED,
            witnesses=(),
            operations=("test_category_prior",),
        ),
    )


def test_calibration_counts_table_falls_out_of_the_charter_schema() -> None:
    """The derived schema gains a ``calibration_counts`` table with the count
    columns — no hand-authored projection catalog, the charter is the projection.
    """

    schema = build_world_sidecar_schema()
    table = schema.table("calibration_counts")
    columns = {column.name for column in table.columns}
    assert {
        "pass_number",
        "category",
        "correct_count",
        "total_count",
    } <= columns


def test_calibration_counts_projection_roundtrips(tmp_path: Path) -> None:
    """A row written through ``add_family`` reads back via the reader in the
    ``(pass_number, category) -> (correct, total)`` shape."""

    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)

    with writable_session(store, schema) as session:
        session.add_family(
            "calibration_counts",
            {
                "calibration_id": calibration_count_id(1, "strong"),
                "pass_number": 1,
                "category": "strong",
                "correct_count": 80,
                "total_count": 100,
            },
        )
        session.commit()

    conn = sqlite3.connect(str(store))
    assert load_calibration_counts(conn) == {(1, "strong"): (80, 100)}


def test_projected_counts_make_categorical_opinion_informative(tmp_path: Path) -> None:
    """The projected counts, read back, drive ``categorical_to_opinion`` away from
    vacuity — the whole point of persisting them."""

    schema = build_world_sidecar_schema()
    store = tmp_path / "world.sqlite"
    create_sqlalchemy_store(store, schema)
    with writable_session(store, schema) as session:
        session.add_family(
            "calibration_counts",
            {
                "calibration_id": calibration_count_id(1, "strong"),
                "pass_number": 1,
                "category": "strong",
                "correct_count": 80,
                "total_count": 100,
            },
        )
        session.commit()

    conn = sqlite3.connect(str(store))
    counts = load_calibration_counts(conn)

    informed = categorical_to_opinion(
        "strong",
        1,
        calibration_counts=counts,
        prior=_category_prior("strong"),
    )
    assert isinstance(informed, Opinion)
    assert informed.u < 1.0
    assert abs(informed.expectation() - 0.8) < 0.1

    # Without the projected counts the same call is honestly vacuous.
    vacuous = categorical_to_opinion("strong", 1, prior=_category_prior("strong"))
    assert isinstance(vacuous, Opinion)
    assert abs(vacuous.u - 1.0) < 1e-9
