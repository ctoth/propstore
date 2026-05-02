"""Concept and form SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3

from propstore.sidecar.stages import ConceptSidecarRows


def populate_concept_sidecar_rows(
    conn: sqlite3.Connection,
    rows: ConceptSidecarRows,
) -> None:
    for row in rows.form_rows:
        conn.execute(
            "INSERT INTO form (name, kind, unit_symbol, is_dimensionless, dimensions) "
            "VALUES (?, ?, ?, ?, ?)",
            row.values,
        )

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

    for row in rows.form_algebra_rows:
        conn.execute(
            "INSERT INTO form_algebra "
            "(output_form, input_forms, operation, source_concept_id, "
            "source_formula, dim_verified) VALUES (?, ?, ?, ?, ?, ?)",
            row.values,
        )

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
