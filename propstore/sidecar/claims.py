"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence

from propstore.sidecar.claim_utils import (
    insert_claim_concept_link_row,
    insert_claim_row,
    insert_claim_stance_row,
)
from propstore.sidecar.stages import (
    ClaimFtsInsertRow,
    ClaimSidecarRows,
    ClaimStanceInsertRow,
    ConflictWitnessInsertRow,
    JustificationInsertRow,
    RawIdQuarantineSidecarRows,
)


def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    for row in rows.claim_rows:
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, target_concept,
                source_slug, source_paper, provenance_page, provenance_json,
                context_id, premise_kind, branch, build_status, stage,
                promotion_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )
    for row in rows.diagnostic_rows:
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )


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

    Bug 5 (v0.3.2): ``artifact_id`` is content-hash-derived, so two
    claim files that carry the same id carry definitionally identical
    claim content. The historical crash path happens when a re-promote
    leaves both the original claim file (``Foo_YEAR_Title.yaml``) and a
    disambiguated copy (``Foo_YEAR_Title--<hex>.yaml``) on disk — both
    contribute rows with the same ``artifact_id``. First-writer-wins
    dedupe is safe here because the content is identical; the UNIQUE
    constraint on ``claim_core.id`` and the PK constraints on the
    three payload tables already enforce that invariant. Reproduction
    in ``tests/remediation/phase_7_race_atomicity/
    test_T7_5f_sidecar_build_duplicate_claim.py``.
    """

    seen_claim_ids: set[str] = set()
    for row in rows.claim_rows:
        claim_id = row.values.get("id")
        if isinstance(claim_id, str) and claim_id in seen_claim_ids:
            continue
        insert_claim_row(conn, row.values)
        if isinstance(claim_id, str):
            seen_claim_ids.add(claim_id)
    for row in rows.claim_link_rows:
        insert_claim_concept_link_row(conn, row.values)
    for stance_row in rows.stance_rows:
        insert_claim_stance_row(conn, stance_row.values)


def populate_stances(
    conn: sqlite3.Connection,
    rows: Sequence[ClaimStanceInsertRow],
) -> None:
    for row in rows:
        insert_claim_stance_row(conn, row.values)


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[JustificationInsertRow],
) -> None:
    for row in rows:
        conn.execute(
            "INSERT OR IGNORE INTO justification "
            "(id, justification_kind, conclusion_claim_id, premise_claim_ids, "
            "source_relation_type, source_claim_id, provenance_json, rule_strength) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ConflictWitnessInsertRow],
) -> None:
    for row in rows:
        conn.execute(
            "INSERT INTO conflict_witness (concept_id, claim_a_id, claim_b_id, "
            "warning_class, conditions_a, conditions_b, value_a, value_b, "
            "derivation_chain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )


def populate_claim_fts_rows(
    conn: sqlite3.Connection,
    rows: Sequence[ClaimFtsInsertRow],
) -> None:
    for row in rows:
        conn.execute(
            "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
            "VALUES (?, ?, ?, ?)",
            row.values,
        )
