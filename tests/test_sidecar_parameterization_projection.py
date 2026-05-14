from __future__ import annotations

import sqlite3

from propstore.sidecar.concepts import (
    PARAMETERIZATION_PROJECTION,
    populate_concept_sidecar_rows,
)
from propstore.sidecar.stages import ConceptSidecarRows


def test_parameterization_rows_use_generated_insert() -> None:
    assert PARAMETERIZATION_PROJECTION.insert_sql() == (
        'INSERT INTO "parameterization" ("output_concept_id", "concept_ids", '
        '"formula", "sympy", "exactness", "conditions_cel", "conditions_ir") '
        "VALUES (:output_concept_id, :concept_ids, :formula, :sympy, :exactness, "
        ":conditions_cel, :conditions_ir)"
    )

    rows = ConceptSidecarRows(
        form_rows=(),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(
            PARAMETERIZATION_PROJECTION.row(
                output_concept_id="concept-alpha",
                concept_ids='["concept-alpha"]',
                formula="x + 1",
                sympy="x + 1",
                exactness="exact",
                conditions_cel="task == 'speech'",
                conditions_ir='{"op":"eq"}',
            ),
        ),
        parameterization_group_rows=(),
        form_algebra_rows=(),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in PARAMETERIZATION_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "parameterization"').fetchone()
    assert dict(stored) == PARAMETERIZATION_PROJECTION.encode_row(rows.parameterization_rows[0])
