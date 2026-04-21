from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_micropublication_missing_claim_quarantines_not_raises(
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
            "source": {"paper": "micropublication_claim"},
            "claims": [
                {
                    "id": "included_claim",
                    "type": "observation",
                    "context": {"id": "ctx_test"},
                    "statement": "Fundamental frequency was observed.",
                    "concepts": [concept_payload["artifact_id"]],
                    "provenance": {"paper": "micropublication_claim", "page": 1},
                },
            ],
        }
    )
    included_claim_id = claim_payload["claims"][0]["artifact_id"]
    missing_claim_id = "ps:claim:missing-micropub"
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
            "claims/micropublication_claim.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
            "contexts/ctx_test.yaml": yaml.dump(
                {"id": "ctx_test", "name": "Test context"},
                sort_keys=False,
            ).encode(),
            "micropubs/bad_claim.yaml": yaml.dump(
                {
                    "micropubs": [
                        {
                            "artifact_id": "ps:micropub:bad-claim",
                            "context": {"id": "ctx_test"},
                            "claims": [included_claim_id, missing_claim_id],
                            "evidence": [
                                {
                                    "kind": "paper_page",
                                    "reference": "micropublication_claim:1",
                                }
                            ],
                            "provenance": {
                                "paper": "micropublication_claim",
                                "page": 1,
                            },
                        }
                    ]
                },
                sort_keys=False,
            ).encode(),
        },
        "seed missing micropublication claim quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        claim_rows = conn.execute(
            "SELECT id FROM claim_core WHERE id = ?",
            (included_claim_id,),
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'micropublication_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert claim_rows == [(included_claim_id,)]
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "micropublication",
        missing_claim_id,
        "micropublication_validation",
        "error",
        1,
    )
    assert "references nonexistent claim" in diagnostic_rows[0][5]
