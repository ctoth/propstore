"""Regression test for Bug 5: UNIQUE violation in sidecar build when
two claim files contribute the same ``artifact_id``.

Reproduces the aspirin ``pks build`` crash (2026-04-23): the aspirin
repository has two claim files (``McNeil_2018_EffectAspirinAll_CauseMortality.yaml``
and ``McNeil_2018_EffectAspirinAll_CauseMortality--5265a1465b03.yaml``)
carrying 43 overlapping ``artifact_id`` values. Because ``artifact_id``
is content-hash-derived, identical ids mean identical claim content —
the build pass must dedupe instead of crashing with
``sqlite3.IntegrityError: UNIQUE constraint failed: claim_core.id``.
"""
from __future__ import annotations

from propstore.sidecar.claims import populate_claims
from propstore.sidecar.schema import (
    create_claim_tables,
    create_context_tables,
)
from propstore.sidecar.sqlite import connect_sidecar
from propstore.sidecar.stages import ClaimInsertRow, ClaimSidecarRows


def _make_claim_row(artifact_id: str, source_paper: str, seq: int) -> dict:
    return {
        "id": artifact_id,
        "primary_logical_id": f"{source_paper}:local-{seq}",
        "logical_ids_json": "[]",
        "version_id": "sha256:deadbeef",
        "seq": seq,
        "type": "observation",
        "target_concept": None,
        "source_slug": source_paper,
        "source_paper": source_paper,
        "provenance_page": 0,
        "provenance_json": None,
        "context_id": None,
        "branch": None,
        "build_status": "ingested",
        "stage": None,
        "promotion_status": None,
        "value": None,
        "lower_bound": None,
        "upper_bound": None,
        "uncertainty": None,
        "uncertainty_type": None,
        "sample_size": None,
        "unit": None,
        "value_si": None,
        "lower_bound_si": None,
        "upper_bound_si": None,
        "conditions_cel": None,
        "statement": "observation",
        "expression": None,
        "sympy_generated": None,
        "sympy_error": None,
        "name": None,
        "measure": None,
        "listener_population": None,
        "methodology": None,
        "notes": None,
        "description": None,
        "auto_summary": None,
        "body": None,
        "canonical_ast": None,
        "variables_json": None,
        "algorithm_stage": None,
    }


def test_populate_claims_tolerates_duplicate_artifact_ids(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_context_tables(conn)
        create_claim_tables(conn)

        # Two rows share the artifact_id. Simulates aspirin's two
        # McNeil claim files that share 43 artifact_ids.
        rows = ClaimSidecarRows(
            claim_rows=(
                ClaimInsertRow(
                    _make_claim_row(
                        "ps:claim:shared0001",
                        "paper-alpha",
                        seq=1,
                    )
                ),
                ClaimInsertRow(
                    _make_claim_row(
                        "ps:claim:shared0001",
                        "paper-alpha-variant",
                        seq=2,
                    )
                ),
            ),
            claim_link_rows=(),
            stance_rows=(),
            quarantine_diagnostics=(),
        )

        populate_claims(conn, rows)
        conn.commit()

        core_rows = conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            ("ps:claim:shared0001",),
        ).fetchall()
        numeric_rows = conn.execute(
            "SELECT claim_id FROM claim_numeric_payload WHERE claim_id = ?",
            ("ps:claim:shared0001",),
        ).fetchall()
        text_rows = conn.execute(
            "SELECT claim_id FROM claim_text_payload WHERE claim_id = ?",
            ("ps:claim:shared0001",),
        ).fetchall()
        algorithm_rows = conn.execute(
            "SELECT claim_id FROM claim_algorithm_payload WHERE claim_id = ?",
            ("ps:claim:shared0001",),
        ).fetchall()
    finally:
        conn.close()

    # Duplicates are collapsed to a single row across the four tables.
    assert len(core_rows) == 1
    assert len(numeric_rows) == 1
    assert len(text_rows) == 1
    assert len(algorithm_rows) == 1
