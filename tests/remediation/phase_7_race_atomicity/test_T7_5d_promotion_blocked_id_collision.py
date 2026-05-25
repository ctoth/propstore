"""Regression test for duplicate promotion-blocked diagnostics.

Promotion-blocked source-local facts mirror a blocked row into ``claim_core``.
The materialized store still must preserve a diagnostic for each source branch
when the same blocked artifact id appears in more than one branch.

The aspirin stance-backfill session (2026-04-23) stacked 15 tangled
re-promote commits because of this — the git commit landed before the
sidecar write, so every failed mirror left master polluted.
"""
from __future__ import annotations

from sqlalchemy import text

from propstore.families.claims.types import ClaimType
from propstore.families.claims.declaration import (
    PromotionBlockedModels,
    compile_promotion_blocked_models,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from propstore.families.registry import world_schema
from quire.sqlalchemy_store import readonly_session
from tests.remediation.phase_7_race_atomicity.promotion_blocked_helpers import (
    create_world_store,
    flush_promotion_blocked,
)


def test_promotion_blocked_mirror_tolerates_prior_row_from_different_branch(
    tmp_path,
):
    sidecar_path = tmp_path / "propstore.sqlite"
    create_world_store(sidecar_path)

    alpha_rows = compile_promotion_blocked_models(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-dup",
                claim_type=ClaimType.OBSERVATION,
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
    beta_rows = compile_promotion_blocked_models(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-dup",
                claim_type=ClaimType.OBSERVATION,
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
    flush_promotion_blocked(
        sidecar_path,
        PromotionBlockedModels(
            claims=alpha_rows.claims + beta_rows.claims,
            diagnostics=alpha_rows.diagnostics + beta_rows.diagnostics,
        ),
    )

    schema = world_schema()
    with readonly_session(sidecar_path, schema) as derived:
        core_rows = derived.session.execute(
            text(
                """
            SELECT id, branch, promotion_status FROM claim_core
            WHERE id = :claim_id ORDER BY branch
            """
            ),
            {"claim_id": "claim-dup"},
        ).all()
        diag_rows = derived.session.execute(
            text(
                """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE claim_id = :claim_id AND diagnostic_kind = 'promotion_blocked'
            ORDER BY source_ref
            """
            ),
            {"claim_id": "claim-dup"},
        ).all()

    # ``claim_core.id`` is the claim identity, so duplicate source-local facts
    # share one blocked row while preserving both branch diagnostics.
    assert core_rows == [("claim-dup", "source/beta", "blocked")]
    assert diag_rows == [
        ("source/alpha:claim-dup", "unresolved in alpha"),
        ("source/beta:claim-dup", "unresolved in beta"),
    ]
