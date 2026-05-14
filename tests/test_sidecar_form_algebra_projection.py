from __future__ import annotations

import json
import sqlite3

from propstore.sidecar.concepts import (
    FORM_ALGEBRA_PROJECTION,
    FORM_PROJECTION,
    populate_concept_sidecar_rows,
)
from propstore.sidecar.stages import ConceptSidecarRows


def test_form_algebra_rows_use_generated_insert_and_autoincrement_id() -> None:
    assert FORM_ALGEBRA_PROJECTION.insert_sql() == (
        'INSERT INTO "form_algebra" ("output_form", "input_forms", "operation", '
        '"source_concept_id", "source_formula", "dim_verified") VALUES '
        "(:output_form, :input_forms, :operation, :source_concept_id, "
        ":source_formula, :dim_verified)"
    )

    rows = ConceptSidecarRows(
        form_rows=(
            FORM_PROJECTION.row(
                name="force",
                kind="quantity",
                unit_symbol="N",
                is_dimensionless=0,
                dimensions='{"M": 1, "L": 1, "T": -2}',
            ),
        ),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(
            FORM_ALGEBRA_PROJECTION.row(
                output_form="force",
                input_forms='["mass", "acceleration"]',
                operation="mass * acceleration",
                source_concept_id="concept-force",
                source_formula="m * a",
                dim_verified=1,
            ),
        ),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for projection in (FORM_PROJECTION, FORM_ALGEBRA_PROJECTION):
        for statement in projection.ddl_statements():
            conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "form_algebra"').fetchone()
    assert stored["id"] == 1
    assert stored["output_form"] == "force"
    assert json.loads(stored["input_forms"]) == ["mass", "acceleration"]
    assert stored["operation"] == "mass * acceleration"
    assert stored["source_concept_id"] == "concept-force"
    assert stored["source_formula"] == "m * a"
    assert stored["dim_verified"] == 1
