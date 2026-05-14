"""Concept and form SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3

from quire.projections import FtsProjection, ProjectionColumn, ProjectionForeignKey, ProjectionIndex, ProjectionTable
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION
from propstore.sidecar.stages import ConceptSidecarRows


CONCEPT_PROJECTION = ProjectionTable(
    name="concept",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("primary_logical_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("logical_ids_json", "TEXT", nullable=False, default_sql="'[]'"),
        ProjectionColumn("version_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("content_hash", "TEXT", nullable=False),
        ProjectionColumn("seq", "INTEGER", nullable=False),
        ProjectionColumn("canonical_name", "TEXT", nullable=False),
        ProjectionColumn("status", "TEXT", nullable=False),
        ProjectionColumn("domain", "TEXT"),
        ProjectionColumn("definition", "TEXT", nullable=False),
        ProjectionColumn("kind_type", "TEXT", nullable=False),
        ProjectionColumn("form", "TEXT", nullable=False),
        ProjectionColumn("form_parameters", "TEXT"),
        ProjectionColumn("range_min", "REAL"),
        ProjectionColumn("range_max", "REAL"),
        ProjectionColumn("is_dimensionless", "INTEGER", nullable=False, default_sql="0"),
        ProjectionColumn("unit_symbol", "TEXT"),
        ProjectionColumn("created_date", "TEXT"),
        ProjectionColumn("last_modified", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
)


FORM_PROJECTION = ProjectionTable(
    name="form",
    columns=(
        ProjectionColumn("name", "TEXT", primary_key=True),
        ProjectionColumn("kind", "TEXT", nullable=False),
        ProjectionColumn("unit_symbol", "TEXT"),
        ProjectionColumn("is_dimensionless", "INTEGER", nullable=False, default_sql="0"),
        ProjectionColumn("dimensions", "TEXT"),
    ),
)


FORM_ALGEBRA_PROJECTION = ProjectionTable(
    name="form_algebra",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("output_form", "TEXT", nullable=False),
        ProjectionColumn("input_forms", "TEXT", nullable=False),
        ProjectionColumn("operation", "TEXT", nullable=False),
        ProjectionColumn("source_concept_id", "TEXT"),
        ProjectionColumn("source_formula", "TEXT"),
        ProjectionColumn("dim_verified", "INTEGER", nullable=False, default_sql="1"),
    ),
    foreign_keys=(
        ProjectionForeignKey(("output_form",), "form", ("name",)),
    ),
    indexes=(ProjectionIndex("idx_form_algebra_output", ("output_form",)),),
)


ALIAS_PROJECTION = ProjectionTable(
    name="alias",
    columns=(
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("alias_name", "TEXT", nullable=False),
        ProjectionColumn("source", "TEXT", nullable=False),
    ),
    foreign_keys=(
        ProjectionForeignKey(("concept_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_alias_name", ("alias_name",)),
        ProjectionIndex("idx_alias_concept", ("concept_id",)),
    ),
)


PARAMETERIZATION_GROUP_PROJECTION = ProjectionTable(
    name="parameterization_group",
    columns=(
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("group_id", "INTEGER", nullable=False),
    ),
    foreign_keys=(
        ProjectionForeignKey(("concept_id",), "concept", ("id",)),
    ),
    indexes=(ProjectionIndex("idx_param_group", ("group_id",)),),
)


PARAMETERIZATION_PROJECTION = ProjectionTable(
    name="parameterization",
    columns=(
        ProjectionColumn("output_concept_id", "TEXT", nullable=False),
        ProjectionColumn("concept_ids", "TEXT", nullable=False),
        ProjectionColumn("formula", "TEXT", nullable=False),
        ProjectionColumn("sympy", "TEXT"),
        ProjectionColumn("exactness", "TEXT", nullable=False),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("conditions_ir", "TEXT"),
    ),
    foreign_keys=(
        ProjectionForeignKey(("output_concept_id",), "concept", ("id",)),
    ),
)


RELATIONSHIP_PROJECTION = ProjectionTable(
    name="relationship",
    columns=(
        ProjectionColumn("source_id", "TEXT", nullable=False),
        ProjectionColumn("type", "TEXT", nullable=False),
        ProjectionColumn("target_id", "TEXT", nullable=False),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("note", "TEXT"),
    ),
    foreign_keys=(
        ProjectionForeignKey(("source_id",), "concept", ("id",)),
        ProjectionForeignKey(("target_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_rel_source", ("source_id",)),
        ProjectionIndex("idx_rel_target", ("target_id",)),
    ),
)


CONCEPT_FTS_PROJECTION = FtsProjection(
    table="concept_fts",
    key_column="concept_id",
    columns=("canonical_name", "aliases", "definition", "conditions"),
    source_query="""
        SELECT
            c.id AS concept_id,
            c.canonical_name AS canonical_name,
            COALESCE(
                (
                    SELECT group_concat(a.alias_name, ' ')
                    FROM alias a
                    WHERE a.concept_id = c.id
                ),
                ''
            ) AS aliases,
            c.definition AS definition,
            COALESCE(
                (
                    SELECT group_concat(value, ' ')
                    FROM (
                        SELECT rel_condition.value AS value
                        FROM relationship r, json_each(r.conditions_cel) AS rel_condition
                        WHERE r.source_id = c.id
                          AND r.conditions_cel IS NOT NULL
                        UNION ALL
                        SELECT param_condition.value AS value
                        FROM parameterization p, json_each(p.conditions_cel) AS param_condition
                        WHERE p.output_concept_id = c.id
                          AND p.conditions_cel IS NOT NULL
                    )
                ),
                ''
            ) AS conditions
        FROM concept c
        ORDER BY c.seq
    """,
)

def populate_concept_sidecar_rows(
    conn: sqlite3.Connection,
    rows: ConceptSidecarRows,
) -> None:
    if rows.form_rows:
        FORM_PROJECTION.insert_rows(conn, rows.form_rows)
    if rows.concept_rows:
        CONCEPT_PROJECTION.insert_rows(conn, rows.concept_rows)
    if rows.alias_rows:
        ALIAS_PROJECTION.insert_rows(conn, rows.alias_rows)

    relationship_insert_sql = RELATIONSHIP_PROJECTION.insert_sql()
    for row in rows.relationship_rows:
        conn.execute(
            relationship_insert_sql,
            {
                "source_id": row.source_id,
                "type": row.relationship_type,
                "target_id": row.target_id,
                "conditions_cel": row.conditions_cel,
                "note": row.note,
            },
        )

    if rows.relation_edge_rows:
        RELATION_EDGE_PROJECTION.insert_rows(conn, rows.relation_edge_rows)
    if rows.parameterization_rows:
        PARAMETERIZATION_PROJECTION.insert_rows(conn, rows.parameterization_rows)
    if rows.parameterization_group_rows:
        PARAMETERIZATION_GROUP_PROJECTION.insert_rows(conn, rows.parameterization_group_rows)
    if rows.form_algebra_rows:
        FORM_ALGEBRA_PROJECTION.insert_rows(conn, rows.form_algebra_rows)
