"""Regression test for promotion-blocked diagnostics with existing claim payloads.

Promotion-blocked source-local facts no longer mirror blocked claim rows into
``claim_core``. If an existing canonical ``claim_core`` row has child payload
rows, the promotion-blocked flush must leave that canonical row and its
children in place while recording the blocking diagnostic.

Reproduces the Belch_2008 crash from the aspirin stance-backfill retry
session (2026-04-23): a claim was ingested in a sibling branch (so its
payload rows exist), and Belch's promote needed to mirror it as
blocked.
"""
from __future__ import annotations

from sqlalchemy import text

from propstore.families.claims.declaration import (
    compile_promotion_blocked_models,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from propstore.families.world_charters import world_sqlalchemy_schema
from quire.sqlalchemy_store import readonly_session, writable_session
from tests.remediation.phase_7_race_atomicity.promotion_blocked_helpers import (
    create_world_store,
    flush_promotion_blocked,
)


def test_promotion_blocked_mirror_replaces_claim_with_existing_payload_children(
    tmp_path,
):
    sidecar_path = tmp_path / "propstore.sqlite"
    create_world_store(sidecar_path)
    schema = world_sqlalchemy_schema()
    with writable_session(sidecar_path, schema) as derived:
        # Seed a claim_core row as a sibling branch would have produced
        # it, with all three payload child tables populated. This is
        # exactly the shape that typed claim write batches produce.
        derived.session.execute(
            text(
                """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id, seq,
                type, target_concept, source_slug,
                source_paper, provenance_page, provenance_json, context_id,
                branch, build_status, stage, promotion_status
            ) VALUES (
                'claim-shared', '', '[]', '', 1,
                'observation', NULL, NULL,
                'paper-alpha', 0, NULL, NULL,
                'source/alpha', 'ingested', NULL, 'promoted'
            )
            """
            )
        )
        derived.session.execute(
            text(
                "INSERT INTO claim_numeric_payload (claim_id, value) "
                "VALUES ('claim-shared', 1.0)"
            )
        )
        derived.session.execute(
            text(
                "INSERT INTO claim_text_payload (claim_id, statement) "
                "VALUES ('claim-shared', 'shared claim statement')"
            )
        )
        derived.session.execute(
            text(
                "INSERT INTO claim_algorithm_payload (claim_id) "
                "VALUES ('claim-shared')"
            )
        )
        # ``claim_concept_link`` also FKs to claim_core(id). The real
        # Unknown_2009 promotion crash hit this child table after the
        # payload-specific cleanup had already landed.
        derived.session.execute(
            text(
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
        )
        derived.session.execute(
            text(
                "INSERT INTO claim_concept_link "
                "(claim_id, concept_id, role, ordinal) "
                "VALUES ('claim-shared', 'concept-alpha', 'target', 0)"
            )
        )
        # Seed a micropublication_claim child too — that table also FKs
        # to claim_core(id). We need a context row first so the
        # micropublication.context_id FK is satisfied.
        derived.session.execute(
            text("INSERT INTO context (id, name) VALUES ('ctx-alpha', 'alpha')")
        )
        derived.session.execute(
            text(
                """
            INSERT INTO micropublication (
                id, context_id, assumptions_json, evidence_json
            ) VALUES ('mp-alpha', 'ctx-alpha', '[]', '[]')
            """
            )
        )
        derived.session.execute(
            text(
                "INSERT INTO micropublication_claim "
                "(micropublication_id, claim_id, seq) "
                "VALUES ('mp-alpha', 'claim-shared', 0)"
            )
        )
        derived.session.commit()

    # Belch_2008 (here ``source/beta``) needs to mirror this claim as
    # blocked. Prior behavior crashes with a FOREIGN KEY violation.
    rows = compile_promotion_blocked_models(
        (
            PromotionBlockedClaimFact(
                artifact_id="claim-shared",
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
    flush_promotion_blocked(sidecar_path, rows)

    with readonly_session(sidecar_path, schema) as derived:
        core_rows = derived.session.execute(
            text(
                """
            SELECT id, branch, promotion_status FROM claim_core
            WHERE id = :claim_id
            """
            ),
            {"claim_id": "claim-shared"},
        ).all()
        child_counts = {
            table_name: derived.session.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE claim_id = :claim_id"),
                {"claim_id": "claim-shared"},
            ).scalar_one()
            for table_name in (
                "claim_numeric_payload",
                "claim_text_payload",
                "claim_algorithm_payload",
                "claim_concept_link",
                "micropublication_claim",
            )
        }
        diag_rows = derived.session.execute(
            text(
                """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE claim_id = :claim_id AND diagnostic_kind = 'promotion_blocked'
            """,
            ),
            {"claim_id": "claim-shared"},
        ).all()

    # Source-local blocked facts stay diagnostics-only; the canonical
    # promoted row and its children are not rewritten.
    assert len(core_rows) == 1, core_rows
    assert core_rows[0][2] == "promoted"
    assert child_counts == {
        "claim_numeric_payload": 1,
        "claim_text_payload": 1,
        "claim_algorithm_payload": 1,
        "claim_concept_link": 1,
        "micropublication_claim": 1,
    }
    assert diag_rows == [
        ("source/beta:claim-shared", "unresolved in beta"),
    ]
