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

from propstore.families.claims.declaration import (
    compile_promotion_blocked_sidecar_rows,
    populate_promotion_blocked_claims,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from quire.derived_runtime import connect_sqlite_store
from tests.sidecar_schema_helpers import build_world_projection_schema


def test_promotion_blocked_mirror_tolerates_prior_row_from_different_branch(
    tmp_path,
):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sqlite_store(sidecar_path)
    try:
        build_world_projection_schema(conn)
    finally:
        conn.close()

    alpha_rows = compile_promotion_blocked_sidecar_rows(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-dup",
                source_branch="source/alpha",
                source_paper="paper-alpha",
                raw_id="local-claim",
                reasons=(
                    PromotionBlockedReason(
                        kind="concept_mapping",
                        detail="unresolved in alpha",
                    ),
                ),
            ),
        )
    )
    beta_rows = compile_promotion_blocked_sidecar_rows(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-dup",
                source_branch="source/beta",
                source_paper="paper-beta",
                raw_id="local-claim",
                reasons=(
                    PromotionBlockedReason(
                        kind="concept_mapping",
                        detail="unresolved in beta",
                    ),
                ),
            ),
        )
    )
    conn = connect_sqlite_store(sidecar_path)
    try:
        populate_promotion_blocked_claims(
            conn,
            alpha_rows.claim_rows + beta_rows.claim_rows,
            alpha_rows.diagnostic_rows + beta_rows.diagnostic_rows,
        )
        conn.commit()
    finally:
        conn.close()

    conn = connect_sqlite_store(sidecar_path)
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
