"""Regression test for Bug 1: claim_core UNIQUE violation when the same
blocked artifact_id is mirrored from a second source branch.

``claim_core.id`` is a ``TEXT PRIMARY KEY``. The prior
The materialized projection must tolerate the same blocked artifact id
from more than one source branch. ``claim_core.id`` is a ``TEXT PRIMARY
KEY``, so the builder must coalesce the claim row while preserving each
branch's diagnostic.

The aspirin stance-backfill session (2026-04-23) stacked 15 tangled
re-promote commits because of this — the git commit landed before the
sidecar write, so every failed mirror left master polluted.
"""
from __future__ import annotations

from types import SimpleNamespace

from propstore.sidecar.build import _populate_promotion_blocked_rows
from propstore.sidecar.schema import create_claim_tables, create_context_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.promote import compile_promotion_blocked_projection_rows


def test_promotion_blocked_mirror_tolerates_prior_row_from_different_branch(
    tmp_path,
):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_context_tables(conn)
        create_claim_tables(conn)
    finally:
        conn.close()

    claim = SimpleNamespace(artifact_id="claim-dup", id="local-claim")

    alpha_rows = compile_promotion_blocked_projection_rows(
        "source/alpha",
        "paper-alpha",
        [claim],
        {"claim-dup": [("concept_mapping", "unresolved in alpha")]},
    )
    beta_rows = compile_promotion_blocked_projection_rows(
        "source/beta",
        "paper-beta",
        [claim],
        {"claim-dup": [("concept_mapping", "unresolved in beta")]},
    )
    conn = connect_sidecar(sidecar_path)
    try:
        _populate_promotion_blocked_rows(
            conn,
            alpha_rows.claim_rows + beta_rows.claim_rows,
            alpha_rows.diagnostic_rows + beta_rows.diagnostic_rows,
        )
        conn.commit()
    finally:
        conn.close()

    conn = connect_sidecar(sidecar_path)
    try:
        core_rows = conn.execute(
            "SELECT id, branch, promotion_status FROM claim_core "
            "WHERE id = ? ORDER BY branch",
            ("claim-dup",),
        ).fetchall()
        diag_rows = conn.execute(
            """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE claim_id = ? AND diagnostic_kind = 'promotion_blocked'
            ORDER BY source_ref
            """,
            ("claim-dup",),
        ).fetchall()
    finally:
        conn.close()

    # There is exactly one claim_core row (id is PK), and both source
    # branches' diagnostic rows are preserved side-by-side.
    assert len(core_rows) == 1, core_rows
    assert core_rows[0][0] == "claim-dup"
    assert core_rows[0][2] == "blocked"
    assert diag_rows == [
        ("source/alpha:claim-dup", "unresolved in alpha"),
        ("source/beta:claim-dup", "unresolved in beta"),
    ]
