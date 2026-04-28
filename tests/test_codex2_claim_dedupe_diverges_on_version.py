from __future__ import annotations

import inspect
from pathlib import Path

from propstore.sidecar.claims import populate_claims
from propstore.sidecar.schema import create_claim_tables, create_context_tables, create_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.sidecar.stages import (
    ClaimConceptLinkInsertRow,
    ClaimInsertRow,
    ClaimSidecarRows,
)


def _claim_row(
    artifact_id: str,
    *,
    version_id: str,
    seq: int = 1,
) -> dict:
    return {
        "id": artifact_id,
        "primary_logical_id": "demo:claim",
        "logical_ids_json": '[{"namespace":"demo","value":"claim"}]',
        "version_id": version_id,
        "seq": seq,
        "type": "observation",
        "target_concept": None,
        "source_slug": "demo",
        "source_paper": "demo",
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


def _open_claim_sidecar(path: Path):
    conn = connect_sidecar(path)
    create_tables(conn)
    create_context_tables(conn)
    create_claim_tables(conn)
    conn.execute(
        """
        INSERT INTO concept (
            id, primary_logical_id, logical_ids_json, version_id,
            content_hash, seq, canonical_name, status, domain, definition,
            kind_type, form, form_parameters, range_min, range_max,
            is_dimensionless, unit_symbol, created_date, last_modified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ps:concept:velocity",
            "demo:velocity",
            "[]",
            "sha256:concept",
            "concept",
            0,
            "velocity",
            "active",
            "demo",
            "Speed with direction.",
            "quantity",
            "quantity",
            None,
            None,
            None,
            0,
            "m/s",
            None,
            None,
        ),
    )
    return conn


def test_populate_claims_detects_same_logical_id_different_version(
    tmp_path: Path,
) -> None:
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = _open_claim_sidecar(sidecar_path)
    try:
        populate_claims(
            conn,
            ClaimSidecarRows(
                claim_rows=(
                    ClaimInsertRow(_claim_row("ps:claim:shared", version_id="sha256:first")),
                    ClaimInsertRow(_claim_row("ps:claim:shared", version_id="sha256:second", seq=2)),
                ),
                claim_link_rows=(),
                stance_rows=(),
                quarantine_diagnostics=(),
            ),
        )
        conn.commit()

        versions = conn.execute(
            "SELECT version_id FROM claim_core WHERE id = ?",
            ("ps:claim:shared",),
        ).fetchall()
        diagnostics = conn.execute(
            "SELECT diagnostic_kind, blocking FROM build_diagnostics WHERE claim_id = ?",
            ("ps:claim:shared",),
        ).fetchall()
    finally:
        conn.close()

    assert versions == [("sha256:first",)]
    assert diagnostics == [("claim_version_conflict", 1)]


def test_populate_claims_dedupes_duplicate_claim_concept_links(
    tmp_path: Path,
) -> None:
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = _open_claim_sidecar(sidecar_path)
    try:
        populate_claims(
            conn,
            ClaimSidecarRows(
                claim_rows=(
                    ClaimInsertRow(_claim_row("ps:claim:linked", version_id="sha256:same")),
                    ClaimInsertRow(_claim_row("ps:claim:linked", version_id="sha256:same")),
                ),
                claim_link_rows=(
                    ClaimConceptLinkInsertRow(
                        ("ps:claim:linked", "ps:concept:velocity", "target", 0, None)
                    ),
                    ClaimConceptLinkInsertRow(
                        ("ps:claim:linked", "ps:concept:velocity", "target", 0, None)
                    ),
                ),
                stance_rows=(),
                quarantine_diagnostics=(),
            ),
        )
        conn.commit()
        link_count = conn.execute(
            "SELECT COUNT(*) FROM claim_concept_link WHERE claim_id = ?",
            ("ps:claim:linked",),
        ).fetchone()[0]
    finally:
        conn.close()

    assert link_count == 1


def test_populate_claims_docstring_names_logical_id_version_contract() -> None:
    docstring = inspect.getdoc(populate_claims) or ""

    assert "artifact_id is the logical id" in docstring
    assert "artifact_id`` is content-hash-derived" not in docstring
