from __future__ import annotations

import sqlite3

from propstore.sidecar.concepts import (
    PARAMETERIZATION_GROUP_PROJECTION,
    populate_concept_sidecar_rows,
)
from propstore.sidecar.stages import ConceptSidecarRows


def test_parameterization_group_rows_use_generated_insert() -> None:
    assert PARAMETERIZATION_GROUP_PROJECTION.insert_sql() == (
        'INSERT INTO "parameterization_group" ("concept_id", "group_id") '
        "VALUES (:concept_id, :group_id)"
    )

    rows = ConceptSidecarRows(
        form_rows=(),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(
            PARAMETERIZATION_GROUP_PROJECTION.row(
                concept_id="concept-alpha",
                group_id=7,
            ),
        ),
        form_algebra_rows=(),
        concept_fts_rows=(),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in PARAMETERIZATION_GROUP_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "parameterization_group"').fetchone()
    assert dict(stored) == {
        "concept_id": "concept-alpha",
        "group_id": 7,
    }
