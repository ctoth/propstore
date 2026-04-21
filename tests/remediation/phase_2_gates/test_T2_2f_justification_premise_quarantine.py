from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_justification_missing_premise_quarantines_not_raises(
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
    claim_payload = normalize_claims_payload(
        {
            "source": {"paper": "justification_premise"},
            "claims": [
                {
                    "id": "conclusion_claim",
                    "type": "observation",
                    "statement": "Fundamental frequency was observed.",
                    "concepts": [concept_payload["artifact_id"]],
                    "provenance": {"paper": "justification_premise", "page": 1},
                },
            ],
        }
    )
    conclusion_claim_id = claim_payload["claims"][0]["artifact_id"]
    missing_premise_id = "ps:claim:missing-premise"
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
            "claims/justification_premise.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
            "contexts/ctx_test.yaml": yaml.dump(
                {"id": "ctx_test", "name": "Test context"},
                sort_keys=False,
            ).encode(),
            "justifications/bad_premise.yaml": yaml.dump(
                {
                    "justifications": [
                        {
                            "id": "just_missing_premise",
                            "conclusion": conclusion_claim_id,
                            "premises": [missing_premise_id],
                            "rule_kind": "empirical_support",
                            "provenance": {"page": 1},
                        }
                    ]
                },
                sort_keys=False,
            ).encode(),
        },
        "seed missing justification premise quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        claim_rows = conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            (conclusion_claim_id,),
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'justification_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert claim_rows == [(conclusion_claim_id,)]
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "justification",
        missing_premise_id,
        "justification_validation",
        "error",
        1,
    )
    assert "references nonexistent premise" in diagnostic_rows[0][5]
