"""Regression test for Bug 4: FK violation when mirroring a blocked
claim whose ``claim_core`` row already has payload child rows.

``_write_promotion_blocked_sidecar_rows`` issues
``DELETE FROM claim_core WHERE id = ?`` with ``PRAGMA foreign_keys = ON``.
If the existing ``claim_core`` row has any child row in
``claim_numeric_payload``, ``claim_text_payload``,
``claim_algorithm_payload``, or ``micropublication_claim`` (all of which
FK to ``claim_core(id)``), the DELETE raises
``sqlite3.IntegrityError: FOREIGN KEY constraint failed`` and the
promote path aborts.

Reproduces the Belch_2008 crash from the aspirin stance-backfill retry
session (2026-04-23): a claim was ingested in a sibling branch (so its
payload rows exist), and Belch's promote needed to mirror it as
blocked.
"""
from __future__ import annotations

from types import SimpleNamespace

from propstore.sidecar.schema import (
    create_tables,
    create_claim_tables,
    create_context_tables,
    create_micropublication_tables,
)
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.promote import _write_promotion_blocked_sidecar_rows


def test_promotion_blocked_mirror_replaces_claim_with_existing_payload_children(
    tmp_path,
):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_tables(conn)
        create_context_tables(conn)
        create_claim_tables(conn)
        create_micropublication_tables(conn)
        # Seed a claim_core row as a sibling branch would have produced
        # it, with all three payload child tables populated. This is
        # exactly the shape that ``insert_claim_row`` produces in
        # ``populate_claims``.
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id, seq,
                type, target_concept, source_slug,
                source_paper, provenance_page, provenance_json, context_id,
                branch, build_status, stage, promotion_status
            ) VALUES (
                'claim-shared', '', '[]', '', 1,
                'observation', NULL, 'paper-alpha',
                'paper-alpha', 0, NULL, NULL,
                'source/alpha', 'ingested', NULL, 'promoted'
            )
            """
        )
        conn.execute(
            "INSERT INTO claim_numeric_payload (claim_id, value) "
            "VALUES ('claim-shared', 1.0)"
        )
        conn.execute(
            "INSERT INTO claim_text_payload (claim_id, statement) "
            "VALUES ('claim-shared', 'shared claim statement')"
        )
        conn.execute(
            "INSERT INTO claim_algorithm_payload (claim_id) "
            "VALUES ('claim-shared')"
        )
        # ``claim_concept_link`` also FKs to claim_core(id). The real
        # Unknown_2009 promotion crash hit this child table after the
        # payload-specific cleanup had already landed.
        conn.execute(
            """
            INSERT INTO concept (
                id, content_hash, seq, canonical_name, status,
                definition, kind_type, form
            ) VALUES (
                'concept-alpha', '', 1, 'alpha', 'active',
                'alpha concept', 'quantity', 'count'
            )
            """
        )
        conn.execute(
            "INSERT INTO claim_concept_link "
            "(claim_id, concept_id, role, ordinal) "
            "VALUES ('claim-shared', 'concept-alpha', 'target', 0)"
        )
        # Seed a micropublication_claim child too — that table also FKs
        # to claim_core(id). We need a context row first so the
        # micropublication.context_id FK is satisfied.
        conn.execute(
            "INSERT INTO context (id, name) VALUES ('ctx-alpha', 'alpha')"
        )
        conn.execute(
            """
            INSERT INTO micropublication (
                id, context_id, assumptions_json, evidence_json
            ) VALUES ('mp-alpha', 'ctx-alpha', '[]', '[]')
            """
        )
        conn.execute(
            "INSERT INTO micropublication_claim "
            "(micropublication_id, claim_id, seq) "
            "VALUES ('mp-alpha', 'claim-shared', 0)"
        )
        conn.commit()
    finally:
        conn.close()

    # Belch_2008 (here ``source/beta``) needs to mirror this claim as
    # blocked. Prior behavior crashes with a FOREIGN KEY violation.
    claim = SimpleNamespace(artifact_id="claim-shared", id="local-claim")
    _write_promotion_blocked_sidecar_rows(
        sidecar_path,
        "source/beta",
        "paper-beta",
        [claim],
        {"claim-shared": [("concept_mapping", "unresolved in beta")]},
    )

    conn = connect_sidecar(sidecar_path)
    try:
        core_rows = conn.execute(
            "SELECT id, branch, promotion_status FROM claim_core "
            "WHERE id = ?",
            ("claim-shared",),
        ).fetchall()
        diag_rows = conn.execute(
            """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE claim_id = ? AND diagnostic_kind = 'promotion_blocked'
            """,
            ("claim-shared",),
        ).fetchall()
    finally:
        conn.close()

    # The mirror row won — the blocked-status row overwrites the prior
    # promoted row (id is PK). Diagnostic is recorded.
    assert len(core_rows) == 1, core_rows
    assert core_rows[0][2] == "blocked"
    assert diag_rows == [
        ("source/beta:claim-shared", "unresolved in beta"),
    ]
