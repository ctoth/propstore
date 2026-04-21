from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_build_repository_claim_validation_error_quarantines_not_raises(
    tmp_path: Path,
) -> None:
    concept_payload = normalize_concept_payloads(
        [
            {
                "id": "concept1",
                "canonical_name": "fundamental_frequency",
                "status": "accepted",
                "definition": "The rate of vocal fold vibration.",
                "domain": "speech",
                "form": "frequency",
            }
        ],
        default_domain="speech",
    )[0]
    missing_target_id = "ps:claim:missing-workflow-target"
    claim_payload = normalize_claims_payload(
        {
            "source": {"paper": "workflow_claim_validation"},
            "claims": [
                {
                    "id": "source_claim",
                    "type": "observation",
                    "context": {"id": "ctx_test"},
                    "statement": "Fundamental frequency was observed.",
                    "concepts": [concept_payload["artifact_id"]],
                    "provenance": {"paper": "workflow_claim_validation", "page": 1},
                    "stances": [
                        {"target": missing_target_id, "type": "rebuts"},
                    ],
                },
            ],
        }
    )
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "forms/frequency.yaml": yaml.dump(
                {"name": "frequency", "dimensionless": False},
                sort_keys=False,
            ).encode(),
            "concepts/fundamental_frequency.yaml": yaml.dump(
                concept_payload,
                sort_keys=False,
            ).encode(),
            "contexts/ctx_test.yaml": yaml.dump(
                {"id": "ctx_test", "name": "Test context"},
                sort_keys=False,
            ).encode(),
            "claims/workflow_claim_validation.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
        },
        "seed compiler workflow claim validation quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    report = build_repository(repo, output=str(sidecar_path), force=True)

    assert report.rebuilt is True
    assert sidecar_path.exists()

    conn = sqlite3.connect(sidecar_path)
    try:
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'stance_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "stance",
        missing_target_id,
        "stance_validation",
        "error",
        1,
    )
    assert "references nonexistent target claim" in diagnostic_rows[0][5]
