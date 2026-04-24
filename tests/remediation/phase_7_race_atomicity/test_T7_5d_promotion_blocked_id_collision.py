"""Regression test for Bug 1: claim_core UNIQUE violation when the same
blocked artifact_id is mirrored from a second source branch.

``claim_core.id`` is a ``TEXT PRIMARY KEY``. The prior
``_write_promotion_blocked_sidecar_rows`` DELETE was scoped by
``(id, branch)``, which does not remove a prior mirror row that came
from a different source branch — so the subsequent INSERT collides on
the primary key and the promote aborts with ``sqlite3.IntegrityError:
UNIQUE constraint failed: claim_core.id``.

The aspirin stance-backfill session (2026-04-23) stacked 15 tangled
re-promote commits because of this — the git commit landed before the
sidecar write, so every failed mirror left master polluted.
"""
from __future__ import annotations

from types import SimpleNamespace

from propstore.sidecar.schema import create_claim_tables, create_context_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.promote import _write_promotion_blocked_sidecar_rows


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

    # First source branch blocks this claim -> mirror row lands with
    # branch='source/alpha'.
    _write_promotion_blocked_sidecar_rows(
        sidecar_path,
        "source/alpha",
        "paper-alpha",
        [claim],
        {"claim-dup": [("concept_mapping", "unresolved in alpha")]},
    )

    # Second, independent source branch also blocks the *same*
    # artifact_id. Prior behavior: DELETE scoped by (id, branch) does
    # not remove the alpha row, INSERT collides on PK.
    _write_promotion_blocked_sidecar_rows(
        sidecar_path,
        "source/beta",
        "paper-beta",
        [claim],
        {"claim-dup": [("concept_mapping", "unresolved in beta")]},
    )

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
