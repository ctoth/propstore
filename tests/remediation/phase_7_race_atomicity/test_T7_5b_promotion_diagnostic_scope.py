from __future__ import annotations

from propstore.families.claims.declaration import (
    PromotionBlockedModels,
    compile_promotion_blocked_models,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from quire.sqlalchemy_store import readonly_session, writable_session
from sqlalchemy import text
from propstore.families.world_charters import world_sqlalchemy_schema
from tests.remediation.phase_7_race_atomicity.promotion_blocked_helpers import (
    create_world_store,
    flush_promotion_blocked,
)


def test_promotion_blocked_diagnostic_delete_is_scoped_to_source_branch(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    create_world_store(sidecar_path)
    schema = world_sqlalchemy_schema()
    with writable_session(sidecar_path, schema) as derived:
        derived.session.execute(
            text(
                """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (
                :claim_id, :source_kind, :source_ref, :diagnostic_kind,
                :severity, :blocking, :message, :file, :detail_json
            )
            """
            ),
            {
                "claim_id": "claim-1",
                "source_kind": "claim",
                "source_ref": "source/a:claim-1",
                "diagnostic_kind": "promotion_blocked",
                "severity": "error",
                "blocking": 1,
                "message": "stale branch a",
                "file": None,
                "detail_json": '{"source_branch": "source/a"}',
            },
        )
        derived.session.execute(
            text(
                """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (
                :claim_id, :source_kind, :source_ref, :diagnostic_kind,
                :severity, :blocking, :message, :file, :detail_json
            )
            """
            ),
            {
                "claim_id": "claim-1",
                "source_kind": "claim",
                "source_ref": "source/b:claim-1",
                "diagnostic_kind": "promotion_blocked",
                "severity": "error",
                "blocking": 1,
                "message": "keep branch b",
                "file": None,
                "detail_json": '{"source_branch": "source/b"}',
            },
        )
        derived.commit()

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

    with readonly_session(sidecar_path, schema) as derived:
        rows = derived.session.execute(
            text(
                """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'promotion_blocked'
            ORDER BY source_ref, message
            """
            )
        ).all()

    assert rows == [
        ("source/a:claim-1", "fresh branch a"),
        ("source/b:claim-1", "keep branch b"),
    ]
