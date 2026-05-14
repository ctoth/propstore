"""Concept and form SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass

from propstore.sidecar.projection import ProjectionColumn, ProjectionForeignKey, ProjectionIndex, ProjectionTable
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
class AliasProjectionRow:
    concept_id: str
    alias_name: str
    source: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "concept_id": self.concept_id,
            "alias_name": self.alias_name,
            "source": self.source,
        }


@dataclass(frozen=True)
class ParameterizationGroupProjectionRow:
    concept_id: str
    group_id: int

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "concept_id": self.concept_id,
            "group_id": self.group_id,
        }


@dataclass(frozen=True)
class ParameterizationProjectionRow:
    output_concept_id: str
    concept_ids: str
    formula: str
    sympy: str | None
    exactness: str
    conditions_cel: str | None
    conditions_ir: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "output_concept_id": self.output_concept_id,
            "concept_ids": self.concept_ids,
            "formula": self.formula,
            "sympy": self.sympy,
            "exactness": self.exactness,
            "conditions_cel": self.conditions_cel,
            "conditions_ir": self.conditions_ir,
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


@dataclass(frozen=True)
class ConceptProjectionRow:
    id: str
    primary_logical_id: str
    logical_ids_json: str
    version_id: str
    content_hash: str
    seq: int
    canonical_name: str
    status: str
    domain: str | None
    definition: str
    kind_type: str
    form: str
    form_parameters: str | None
    range_min: float | None
    range_max: float | None
    is_dimensionless: int
    unit_symbol: str | None
    created_date: str | None
    last_modified: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "primary_logical_id": self.primary_logical_id,
            "logical_ids_json": self.logical_ids_json,
            "version_id": self.version_id,
            "content_hash": self.content_hash,
            "seq": self.seq,
            "canonical_name": self.canonical_name,
            "status": self.status,
            "domain": self.domain,
            "definition": self.definition,
            "kind_type": self.kind_type,
            "form": self.form,
            "form_parameters": self.form_parameters,
            "range_min": self.range_min,
            "range_max": self.range_max,
            "is_dimensionless": self.is_dimensionless,
            "unit_symbol": self.unit_symbol,
            "created_date": self.created_date,
            "last_modified": self.last_modified,
        }


def populate_concept_sidecar_rows(
    conn: sqlite3.Connection,
    rows: ConceptSidecarRows,
) -> None:
    form_insert_sql = FORM_PROJECTION.insert_sql()
    for row in rows.form_rows:
        conn.execute(form_insert_sql, row.as_insert_mapping())

    concept_insert_sql = CONCEPT_PROJECTION.insert_sql()
    for row in rows.concept_rows:
        conn.execute(concept_insert_sql, row.as_insert_mapping())

    alias_insert_sql = ALIAS_PROJECTION.insert_sql()
    for row in rows.alias_rows:
        conn.execute(alias_insert_sql, row.as_insert_mapping())

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

    parameterization_insert_sql = PARAMETERIZATION_PROJECTION.insert_sql()
    for row in rows.parameterization_rows:
        conn.execute(parameterization_insert_sql, row.as_insert_mapping())

    parameterization_group_insert_sql = PARAMETERIZATION_GROUP_PROJECTION.insert_sql()
    for row in rows.parameterization_group_rows:
        conn.execute(parameterization_group_insert_sql, row.as_insert_mapping())

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
