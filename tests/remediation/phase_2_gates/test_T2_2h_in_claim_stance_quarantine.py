from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_in_claim_stance_missing_target_quarantines_not_raises(
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
    missing_target_id = "ps:claim:missing-inline-stance"
    claim_payload = normalize_claims_payload(
        {
            "source": {"paper": "inline_stance"},
            "claims": [
                {
                    "id": "source_claim",
                    "type": "observation",
                    "context": {"id": "ctx_test"},
                    "statement": "Fundamental frequency was observed.",
                    "concepts": [concept_payload["artifact_id"]],
                    "provenance": {"paper": "inline_stance", "page": 1},
                    "stances": [
                        {"target": missing_target_id, "type": "rebuts"},
                    ],
                },
            ],
        }
    )
    source_claim_id = claim_payload["claims"][0]["artifact_id"]
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
            "claims/inline_stance.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
            "contexts/ctx_test.yaml": yaml.dump(
                {"id": "ctx_test", "name": "Test context"},
                sort_keys=False,
            ).encode(),
        },
        "seed missing in-claim stance target quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        claim_rows = conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            (source_claim_id,),
        ).fetchall()
        stance_rows = conn.execute(
            "SELECT claim_id, target_claim_id FROM claim_stance"
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'stance_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert claim_rows == [(source_claim_id,)]
    assert stance_rows == []
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "stance",
        missing_target_id,
        "stance_validation",
        "error",
        1,
    )
    assert "references nonexistent target claim" in diagnostic_rows[0][5]
