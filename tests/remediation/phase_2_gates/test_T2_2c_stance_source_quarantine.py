from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_stance_file_missing_source_claim_quarantines_not_raises(
    tmp_path: Path,
) -> None:
    claim_payload = normalize_claims_payload(
        {
            "source": {"paper": "stance_source"},
            "claims": [
                {
                    "id": "target_claim",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "stance_source", "page": 1},
                },
            ],
        }
    )
    target_claim_id = claim_payload["claims"][0]["artifact_id"]
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
            "claims/stance_source.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
            "stances/ps__claim__missing.yaml": yaml.dump(
                {
                    "source_claim": "ps:claim:missing",
                    "stances": [{"target": target_claim_id, "type": "rebuts"}],
                },
                sort_keys=False,
            ).encode(),
        },
        "seed missing stance source quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        claim_rows = conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            (target_claim_id,),
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

    assert claim_rows == [(target_claim_id,)]
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "stance",
        "ps:claim:missing",
        "stance_validation",
        "error",
        1,
    )
    assert "references nonexistent source claim" in diagnostic_rows[0][5]
