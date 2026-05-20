from __future__ import annotations

from propstore.families.claims.declaration import (
    PromotionBlockedModels,
    compile_promotion_blocked_models,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from quire.derived_runtime import connect_sqlite_store
from tests.remediation.phase_7_race_atomicity.promotion_blocked_helpers import (
    create_world_store,
    flush_promotion_blocked,
)


def test_promotion_blocked_diagnostic_delete_is_scoped_to_source_branch(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    create_world_store(sidecar_path)
    conn = connect_sqlite_store(sidecar_path)
    try:
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

    alpha_rows = compile_promotion_blocked_models(
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
    beta_rows = compile_promotion_blocked_models(
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
    flush_promotion_blocked(
        sidecar_path,
        PromotionBlockedModels(
            claims=alpha_rows.claims + beta_rows.claims,
            diagnostics=alpha_rows.diagnostics + beta_rows.diagnostics,
        ),
    )

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
