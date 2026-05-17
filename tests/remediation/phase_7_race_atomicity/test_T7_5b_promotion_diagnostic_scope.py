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


def test_promotion_blocked_diagnostic_delete_is_scoped_to_source_branch(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sqlite_store(sidecar_path)
    try:
        build_world_projection_schema(conn)
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "claim-1",
                "claim",
                "source/a:claim-1",
                "promotion_blocked",
                "error",
                1,
                "stale branch a",
                None,
                '{"source_branch": "source/a"}',
            ),
        )
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "claim-1",
                "claim",
                "source/b:claim-1",
                "promotion_blocked",
                "error",
                1,
                "keep branch b",
                None,
                '{"source_branch": "source/b"}',
            ),
        )
        conn.commit()
    finally:
        conn.close()

    alpha_rows = compile_promotion_blocked_sidecar_rows(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-1",
                source_branch="source/a",
                source_paper="paper-a",
                raw_id="local-claim",
                reasons=(
                    PromotionBlockedReason(
                        kind="concept_mapping",
                        detail="fresh branch a",
                    ),
                ),
            ),
        )
    )
    beta_rows = compile_promotion_blocked_sidecar_rows(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-1",
                source_branch="source/b",
                source_paper="paper-b",
                raw_id="local-claim",
                reasons=(
                    PromotionBlockedReason(
                        kind="concept_mapping",
                        detail="keep branch b",
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
        rows = conn.execute(
            """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'promotion_blocked'
            ORDER BY source_ref, message
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("source/a:claim-1", "fresh branch a"),
        ("source/b:claim-1", "keep branch b"),
    ]
