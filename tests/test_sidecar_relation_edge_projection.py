from __future__ import annotations

import sqlite3

from propstore.sidecar.concepts import populate_concept_sidecar_rows
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION, RelationEdgeProjectionRow
from propstore.sidecar.stages import ConceptSidecarRows


def test_concept_relation_edge_rows_use_generated_insert() -> None:
    rows = ConceptSidecarRows(
        form_rows=(),
        concept_rows=(),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(
            RelationEdgeProjectionRow(
                source_kind="concept",
                source_id="concept-a",
                relation_type="broader",
                target_kind="concept",
                target_id="concept-b",
                conditions_cel=None,
                note="taxonomy",
            ),
        ),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(),
        concept_fts_rows=(),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in RELATION_EDGE_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute(
        'SELECT source_kind, source_id, relation_type, target_kind, target_id, '
        'conditions_cel, note FROM "relation_edge"'
    ).fetchone()
    assert dict(stored) == {
        "source_kind": "concept",
        "source_id": "concept-a",
        "relation_type": "broader",
        "target_kind": "concept",
        "target_id": "concept-b",
        "conditions_cel": None,
        "note": "taxonomy",
    }
