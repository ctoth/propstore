from __future__ import annotations

import sqlite3

import pytest
import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def _seed_claim_repo(root) -> Repository:
    repo = Repository.init(root)
    concept = normalize_concept_payloads(
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
    claims = normalize_claims_payload(
        {
            "source": {
                "paper": "sidecar_exception_test",
                "extraction_model": "test",
                "extraction_date": "2026-01-01",
            },
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": concept["artifact_id"],
                    "concepts": [concept["artifact_id"]],
                    "value": 120.0,
                    "unit": "Hz",
                    "provenance": {"paper": "sidecar_exception_test", "page": 1},
                }
            ],
        }
    )
    repo.git.commit_files(
        {
            "forms/frequency.yaml": yaml.dump(
                {"name": "frequency", "dimensionless": False},
                sort_keys=False,
            ).encode(),
            "concepts/fundamental_frequency.yaml": yaml.dump(
                concept,
                sort_keys=False,
            ).encode(),
            "claims/claim.yaml": yaml.dump(claims, sort_keys=False).encode(),
        },
        "seed sidecar exception test",
    )
    return repo


def test_sidecar_not_deleted_on_build_exception(tmp_path, monkeypatch) -> None:
    repo = _seed_claim_repo(tmp_path / "knowledge")
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    def fail_populate_claims(*args, **kwargs) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr("propstore.sidecar.build.populate_claims", fail_populate_claims)

    with pytest.raises(RuntimeError, match="boom"):
        build_sidecar(repo, sidecar_path, force=True)

    assert sidecar_path.exists(), "sidecar deleted on partial-build failure"
    conn = sqlite3.connect(sidecar_path)
    try:
        rows = conn.execute(
            "SELECT diagnostic_kind, severity, blocking, message "
            "FROM build_diagnostics WHERE diagnostic_kind='build_exception'"
        ).fetchall()
    finally:
        conn.close()

    assert rows
    assert rows[0][1:] == ("error", 1, "boom")
