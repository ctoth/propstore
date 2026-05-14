"""Concept and form SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass

from propstore.sidecar.projection import ProjectionColumn, ProjectionForeignKey, ProjectionIndex, ProjectionTable
from propstore.sidecar.stages import ConceptSidecarRows


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


@dataclass(frozen=True)
class FormProjectionRow:
    name: str
    kind: str
    unit_symbol: str | None
    is_dimensionless: int
    dimensions: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "unit_symbol": self.unit_symbol,
            "is_dimensionless": self.is_dimensionless,
            "dimensions": self.dimensions,
        }


@dataclass(frozen=True)
class FormAlgebraProjectionRow:
    output_form: str
    input_forms: str
    operation: str
    source_concept_id: str | None
    source_formula: str | None
    dim_verified: int

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "output_form": self.output_form,
            "input_forms": self.input_forms,
            "operation": self.operation,
            "source_concept_id": self.source_concept_id,
            "source_formula": self.source_formula,
            "dim_verified": self.dim_verified,
        }


def populate_concept_sidecar_rows(
    conn: sqlite3.Connection,
    rows: ConceptSidecarRows,
) -> None:
    form_insert_sql = FORM_PROJECTION.insert_sql()
    for row in rows.form_rows:
        conn.execute(form_insert_sql, row.as_insert_mapping())

    for row in rows.concept_rows:
        conn.execute(
            "INSERT INTO concept (id, primary_logical_id, logical_ids_json, "
            "version_id, content_hash, seq, canonical_name, status, domain, "
            "definition, kind_type, form, form_parameters, range_min, range_max, "
            "is_dimensionless, unit_symbol, created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )

    for row in rows.alias_rows:
        conn.execute(
            "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
            row.values,
        )

    for row in rows.relationship_rows:
        conn.execute(
            "INSERT INTO relationship "
            "(source_id, type, target_id, conditions_cel, note) "
            "VALUES (?, ?, ?, ?, ?)",
            row.values,
        )

    for row in rows.relation_edge_rows:
        conn.execute(
            "INSERT INTO relation_edge "
            "(source_kind, source_id, relation_type, target_kind, target_id, "
            "conditions_cel, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )

    for row in rows.parameterization_rows:
        conn.execute(
            "INSERT INTO parameterization "
            "(output_concept_id, concept_ids, formula, sympy, exactness, "
            "conditions_cel, conditions_ir) VALUES (?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )

    for row in rows.parameterization_group_rows:
        conn.execute(
            "INSERT INTO parameterization_group (concept_id, group_id) "
            "VALUES (?, ?)",
            row.values,
        )

    form_algebra_insert_sql = FORM_ALGEBRA_PROJECTION.insert_sql()
    for row in rows.form_algebra_rows:
        conn.execute(form_algebra_insert_sql, row.as_insert_mapping())

    conn.execute(
        """
        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        )
        """
    )
    for row in rows.concept_fts_rows:
        conn.execute(
            "INSERT INTO concept_fts "
            "(concept_id, canonical_name, aliases, definition, conditions) "
            "VALUES (?, ?, ?, ?, ?)",
            row.values,
        )
