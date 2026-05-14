from __future__ import annotations

import inspect
from pathlib import Path

from propstore.sidecar.claims import (
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_CORE_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    populate_claims,
)
from propstore.sidecar.schema import create_claim_tables, create_context_tables, create_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.sidecar.stages import ClaimSidecarRows


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
        "conditions_ir": None,
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


def _claim_sidecar_rows(
    *claim_rows: dict,
    claim_link_rows: tuple = (),
) -> ClaimSidecarRows:
    return ClaimSidecarRows(
        claim_core_rows=tuple(_claim_core_row(row) for row in claim_rows),
        numeric_payload_rows=tuple(
            CLAIM_NUMERIC_PAYLOAD_PROJECTION.row(
                claim_id=row["id"],
                value=row["value"],
                lower_bound=row["lower_bound"],
                upper_bound=row["upper_bound"],
                uncertainty=row["uncertainty"],
                uncertainty_type=row["uncertainty_type"],
                sample_size=row["sample_size"],
                unit=row["unit"],
                value_si=row["value_si"],
                lower_bound_si=row["lower_bound_si"],
                upper_bound_si=row["upper_bound_si"],
            )
            for row in claim_rows
        ),
        text_payload_rows=tuple(
            CLAIM_TEXT_PAYLOAD_PROJECTION.row(
                claim_id=row["id"],
                conditions_cel=row["conditions_cel"],
                conditions_ir=row["conditions_ir"],
                statement=row["statement"],
                expression=row["expression"],
                sympy_generated=row["sympy_generated"],
                sympy_error=row["sympy_error"],
                name=row["name"],
                measure=row["measure"],
                listener_population=row["listener_population"],
                methodology=row["methodology"],
                notes=row["notes"],
                description=row["description"],
                auto_summary=row["auto_summary"],
            )
            for row in claim_rows
        ),
        algorithm_payload_rows=tuple(
            CLAIM_ALGORITHM_PAYLOAD_PROJECTION.row(
                claim_id=row["id"],
                body=row["body"],
                canonical_ast=row["canonical_ast"],
                variables_json=row["variables_json"],
                algorithm_stage=row["algorithm_stage"],
            )
            for row in claim_rows
        ),
        claim_link_rows=claim_link_rows,
        stance_rows=(),
        quarantine_diagnostics=(),
    )


def _claim_core_row(row: dict):
    return CLAIM_CORE_PROJECTION.row(
        id=row["id"],
        primary_logical_id=row["primary_logical_id"],
        logical_ids_json=row["logical_ids_json"],
        version_id=row["version_id"],
        content_hash=row.get("content_hash") or "",
        seq=row["seq"],
        type=row["type"],
        target_concept=row["target_concept"],
        source_slug=row["source_slug"],
        source_paper=row["source_paper"],
        provenance_page=row["provenance_page"],
        provenance_json=row["provenance_json"],
        context_id=row["context_id"],
        premise_kind=row.get("premise_kind") or "ordinary",
        branch=row.get("branch"),
        build_status=row.get("build_status") or "ingested",
        stage=row.get("stage"),
        promotion_status=row.get("promotion_status"),
    )


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
            _claim_sidecar_rows(
                _claim_row("ps:claim:shared", version_id="sha256:first"),
                _claim_row(
                    "ps:claim:shared",
                    version_id="sha256:second",
                    seq=2,
                ),
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
            _claim_sidecar_rows(
                _claim_row("ps:claim:linked", version_id="sha256:same"),
                _claim_row("ps:claim:linked", version_id="sha256:same"),
                claim_link_rows=(
                    CLAIM_CONCEPT_LINK_PROJECTION.row(
                        claim_id="ps:claim:linked",
                        concept_id="ps:concept:velocity",
                        role="target",
                        ordinal=0,
                        binding_name=None,
                    ),
                    CLAIM_CONCEPT_LINK_PROJECTION.row(
                        claim_id="ps:claim:linked",
                        concept_id="ps:concept:velocity",
                        role="target",
                        ordinal=0,
                        binding_name=None,
                    ),
                ),
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
