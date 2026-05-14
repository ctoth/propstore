from __future__ import annotations

import json
import sqlite3

from propstore.core.conditions.registry import KindType
from propstore.families.forms.stages import FormDefinition
from propstore.sidecar.concepts import FORM_PROJECTION, populate_concept_sidecar_rows
from propstore.sidecar.passes import compile_concept_sidecar_rows


def test_form_rows_are_projection_rows_and_round_trip_dimensions() -> None:
    rows = compile_concept_sidecar_rows(
        concepts=[],
        form_registry={
            "length": FormDefinition(
                name="length",
                kind=KindType.QUANTITY,
                unit_symbol="m",
                dimensions={"L": 1},
            )
        },
        cel_registry={},
    )

    assert rows.form_rows == (
        FORM_PROJECTION.row(
            name="length",
            kind="quantity",
            unit_symbol="m",
            is_dimensionless=0,
            dimensions='{"L": 1}',
        ),
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in FORM_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "form" WHERE name = ?', ("length",)).fetchone()
    assert stored["kind"] == "quantity"
    assert stored["unit_symbol"] == "m"
    assert stored["is_dimensionless"] == 0
    assert json.loads(stored["dimensions"]) == {"L": 1}
