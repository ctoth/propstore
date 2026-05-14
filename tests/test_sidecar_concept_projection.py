from __future__ import annotations

import sqlite3

from propstore.sidecar.concepts import (
    CONCEPT_PROJECTION,
    populate_concept_sidecar_rows,
)
from propstore.sidecar.stages import ConceptSidecarRows


def test_concept_rows_use_generated_ddl_and_insert() -> None:
    assert CONCEPT_PROJECTION.insert_sql() == (
        'INSERT INTO "concept" ("id", "primary_logical_id", "logical_ids_json", '
        '"version_id", "content_hash", "seq", "canonical_name", "status", "domain", '
        '"definition", "kind_type", "form", "form_parameters", "range_min", '
        '"range_max", "is_dimensionless", "unit_symbol", "created_date", '
        '"last_modified") VALUES (:id, :primary_logical_id, :logical_ids_json, '
        ':version_id, :content_hash, :seq, :canonical_name, :status, :domain, '
        ':definition, :kind_type, :form, :form_parameters, :range_min, :range_max, '
        ':is_dimensionless, :unit_symbol, :created_date, :last_modified)'
    )

    rows = ConceptSidecarRows(
        form_rows=(),
        concept_rows=(
            CONCEPT_PROJECTION.row(
                id="concept-alpha",
                primary_logical_id="logical-alpha",
                logical_ids_json='["logical-alpha"]',
                version_id="sha256:abc",
                content_hash="abc",
                seq=1,
                canonical_name="alpha",
                status="accepted",
                domain="speech",
                definition="Alpha concept.",
                kind_type="scalar",
                form="number",
                form_parameters=None,
                range_min=None,
                range_max=None,
                is_dimensionless=1,
                unit_symbol=None,
                created_date=None,
                last_modified=None,
            ),
        ),
        alias_rows=(),
        relationship_rows=(),
        relation_edge_rows=(),
        parameterization_rows=(),
        parameterization_group_rows=(),
        form_algebra_rows=(),
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in CONCEPT_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_concept_sidecar_rows(conn, rows)

    stored = conn.execute('SELECT * FROM "concept"').fetchone()
    assert dict(stored) == CONCEPT_PROJECTION.encode_row(rows.concept_rows[0])
