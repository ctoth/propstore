"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence

from quire.projections import (
    FtsProjection,
    ProjectionColumn,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
)
from propstore.sidecar.diagnostics import (
    BUILD_DIAGNOSTICS_PROJECTION,
    insert_build_diagnostic,
)
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION
from propstore.sidecar.stages import (
    ClaimSidecarRows,
    RawIdQuarantineSidecarRows,
)

CLAIM_CORE_PROJECTION = ProjectionTable(
    name="claim_core",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("primary_logical_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("logical_ids_json", "TEXT", nullable=False, default_sql="'[]'"),
        ProjectionColumn("version_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("content_hash", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("seq", "INTEGER", nullable=False),
        ProjectionColumn("type", "TEXT", nullable=False),
        ProjectionColumn("target_concept", "TEXT"),
        ProjectionColumn("source_slug", "TEXT"),
        ProjectionColumn("source_paper", "TEXT", nullable=False),
        ProjectionColumn("provenance_page", "INTEGER", nullable=False),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("context_id", "TEXT"),
        ProjectionColumn("premise_kind", "TEXT", nullable=False, default_sql="'ordinary'"),
        ProjectionColumn("branch", "TEXT"),
        ProjectionColumn("build_status", "TEXT", nullable=False, default_sql="'ingested'"),
        ProjectionColumn("stage", "TEXT"),
        ProjectionColumn("promotion_status", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(
        ProjectionIndex("idx_claim_core_target", ("target_concept",)),
        ProjectionIndex("idx_claim_core_type", ("type",)),
        ProjectionIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)),
        ProjectionIndex("idx_claim_core_build_status", ("build_status",)),
        ProjectionIndex("idx_claim_core_stage", ("stage",)),
        ProjectionIndex("idx_claim_core_promotion_status", ("promotion_status",)),
    ),
)


CLAIM_CONCEPT_LINK_PROJECTION = ProjectionTable(
    name="claim_concept_link",
    columns=(
        ProjectionColumn("claim_id", "TEXT", nullable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("role", "TEXT", nullable=False),
        ProjectionColumn("ordinal", "INTEGER", nullable=False),
        ProjectionColumn("binding_name", "TEXT"),
    ),
    primary_key=("claim_id", "role", "ordinal", "concept_id"),
    foreign_keys=(
        ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),
        ProjectionForeignKey(("concept_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_claim_concept_link_claim", ("claim_id",)),
        ProjectionIndex("idx_claim_concept_link_concept", ("concept_id",)),
        ProjectionIndex("idx_claim_concept_link_role", ("role",)),
    ),
)


CLAIM_NUMERIC_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_numeric_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("value", "REAL"),
        ProjectionColumn("lower_bound", "REAL"),
        ProjectionColumn("upper_bound", "REAL"),
        ProjectionColumn("uncertainty", "REAL"),
        ProjectionColumn("uncertainty_type", "TEXT"),
        ProjectionColumn("sample_size", "INTEGER"),
        ProjectionColumn("unit", "TEXT"),
        ProjectionColumn("value_si", "REAL"),
        ProjectionColumn("lower_bound_si", "REAL"),
        ProjectionColumn("upper_bound_si", "REAL"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_TEXT_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_text_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("conditions_ir", "TEXT"),
        ProjectionColumn("statement", "TEXT"),
        ProjectionColumn("expression", "TEXT"),
        ProjectionColumn("sympy_generated", "TEXT"),
        ProjectionColumn("sympy_error", "TEXT"),
        ProjectionColumn("name", "TEXT"),
        ProjectionColumn("measure", "TEXT"),
        ProjectionColumn("listener_population", "TEXT"),
        ProjectionColumn("methodology", "TEXT"),
        ProjectionColumn("notes", "TEXT"),
        ProjectionColumn("description", "TEXT"),
        ProjectionColumn("auto_summary", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_ALGORITHM_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_algorithm_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("body", "TEXT"),
        ProjectionColumn("canonical_ast", "TEXT"),
        ProjectionColumn("variables_json", "TEXT"),
        ProjectionColumn("algorithm_stage", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
    indexes=(ProjectionIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
)


CONFLICT_WITNESS_PROJECTION = ProjectionTable(
    name="conflict_witness",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("claim_a_id", "TEXT", nullable=False),
        ProjectionColumn("claim_b_id", "TEXT", nullable=False),
        ProjectionColumn("warning_class", "TEXT", nullable=False),
        ProjectionColumn("conditions_a", "TEXT"),
        ProjectionColumn("conditions_b", "TEXT"),
        ProjectionColumn("value_a", "TEXT"),
        ProjectionColumn("value_b", "TEXT"),
        ProjectionColumn("derivation_chain", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_conflict_witness_concept", ("concept_id",)),),
)


JUSTIFICATION_PROJECTION = ProjectionTable(
    name="justification",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("justification_kind", "TEXT", nullable=False),
        ProjectionColumn("conclusion_claim_id", "TEXT", nullable=False),
        ProjectionColumn("premise_claim_ids", "TEXT", nullable=False),
        ProjectionColumn("source_relation_type", "TEXT"),
        ProjectionColumn("source_claim_id", "TEXT"),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("rule_strength", "TEXT", nullable=False, default_sql="'defeasible'"),
    ),
)


CLAIM_FTS_PROJECTION = FtsProjection(
    table="claim_fts",
    key_column="claim_id",
    columns=("statement", "conditions", "expression"),
    source_query="""
        SELECT
            c.id AS claim_id,
            COALESCE(t.statement, '') AS statement,
            COALESCE(
                (
                    SELECT group_concat(value, ' ')
                    FROM json_each(t.conditions_cel)
                ),
                ''
            ) AS conditions,
            COALESCE(t.expression, '') AS expression
        FROM claim_core c
        JOIN claim_text_payload t ON t.claim_id = c.id
        ORDER BY c.seq
    """,
)

def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    CLAIM_CORE_PROJECTION.insert_rows(conn, (row.values for row in rows.claim_rows))
    for row in rows.diagnostic_rows:
        insert_build_diagnostic(conn, row)


def populate_claims(
    conn: sqlite3.Connection,
    rows: ClaimSidecarRows,
) -> None:
    """Populate normalized claim storage from compiled sidecar rows.

    Schema-v3 behavior (``reviews/2026-04-16-code-review/workstreams/
    ws-z-render-gates.md`` finding 3.2): the file-level ``stage`` marker
    (e.g. ``'draft'``) is threaded from the claim-file document onto each
    ``claim_core`` row. Drafts populate normally; render-policy filtering
    (phase 4) decides visibility.

    ``artifact_id is the logical id`` for a claim. ``version_id`` is the
    content identity. Duplicate rows with the same ``artifact_id`` and
    same ``version_id`` are idempotent; duplicate logical ids with
    different versions emit a blocking ``claim_version_conflict``
    diagnostic instead of silently taking the first writer.
    """

    seen_claim_versions: dict[str, str] = {}
    emitted_conflicts: set[tuple[str, str, str]] = set()
    payloads_by_claim_id = {
        numeric_row.values["claim_id"]: (numeric_row, text_row, algorithm_row)
        for numeric_row, text_row, algorithm_row in zip(
            rows.numeric_payload_rows,
            rows.text_payload_rows,
            rows.algorithm_payload_rows,
            strict=True,
        )
    }
    for row in rows.claim_core_rows:
        claim_id = row.values.get("id")
        version_id = row.values.get("version_id")
        if isinstance(claim_id, str) and claim_id in seen_claim_versions:
            existing_version = seen_claim_versions[claim_id]
            new_version = str(version_id or "")
            if existing_version == new_version:
                continue
            conflict_key = (claim_id, existing_version, new_version)
            if conflict_key not in emitted_conflicts:
                _insert_claim_version_conflict(
                    conn,
                    claim_id=claim_id,
                    existing_version=existing_version,
                    new_version=new_version,
                    source_ref=str(row.values.get("primary_logical_id") or claim_id),
                )
                emitted_conflicts.add(conflict_key)
            continue
        CLAIM_CORE_PROJECTION.insert_row(conn, row.values)
        numeric_row, text_row, algorithm_row = payloads_by_claim_id[claim_id]
        CLAIM_NUMERIC_PAYLOAD_PROJECTION.insert_row(conn, numeric_row.values)
        CLAIM_TEXT_PAYLOAD_PROJECTION.insert_row(conn, text_row.values)
        CLAIM_ALGORITHM_PAYLOAD_PROJECTION.insert_row(conn, algorithm_row.values)
        if isinstance(claim_id, str):
            seen_claim_versions[claim_id] = str(version_id or "")
    seen_link_keys: set[tuple[object, object, object, object]] = set()
    for row in rows.claim_link_rows:
        key = (
            row.values["claim_id"],
            row.values["role"],
            row.values["ordinal"],
            row.values["concept_id"],
        )
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        CLAIM_CONCEPT_LINK_PROJECTION.insert_row(conn, row)
    if rows.stance_rows:
        RELATION_EDGE_PROJECTION.insert_rows(conn, (stance_row.values for stance_row in rows.stance_rows))


def _insert_claim_version_conflict(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    existing_version: str,
    new_version: str,
    source_ref: str,
) -> None:
    insert_build_diagnostic(
        conn,
        BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=claim_id,
            source_kind="claim",
            source_ref=source_ref,
            diagnostic_kind="claim_version_conflict",
            severity="error",
            blocking=1,
            message=f"Claim logical id {claim_id!r} appears with multiple version_id values",
            file=None,
            detail_json=json.dumps(
                {
                    "existing_version_id": existing_version,
                    "new_version_id": new_version,
                },
                sort_keys=True,
            ),
        ),
    )


def populate_stances(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    RELATION_EDGE_PROJECTION.insert_rows(conn, (row.values for row in rows))


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    JUSTIFICATION_PROJECTION.insert_rows(conn, rows, or_ignore=True)


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    CONFLICT_WITNESS_PROJECTION.insert_rows(conn, rows)
