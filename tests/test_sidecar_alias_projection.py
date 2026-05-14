from __future__ import annotations

import sqlite3

from propstore.sidecar.concepts import ALIAS_PROJECTION, populate_concept_sidecar_rows
from propstore.sidecar.stages import ConceptSidecarRows


def test_alias_rows_use_generated_insert() -> None:
    assert ALIAS_PROJECTION.insert_sql() == (
        'INSERT INTO "alias" ("concept_id", "alias_name", "source") '
        "VALUES (:concept_id, :alias_name, :source)"
    )

    rows = ConceptSidecarRows(
        form_rows=(),
        concept_rows=(),
        alias_rows=(
            ALIAS_PROJECTION.row(
                concept_id="concept-alpha",
                alias_name="F0",
                source="Sundberg_1993",
            ),
        ),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(),
        concept_fts_rows=(),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in ALIAS_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "alias"').fetchone()
    assert dict(stored) == {
        "concept_id": "concept-alpha",
        "alias_name": "F0",
        "source": "Sundberg_1993",
    }
