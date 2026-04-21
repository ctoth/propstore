from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.families.claims.stages import ClaimStage
from propstore.families.registry import PropstoreFamily
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic, PipelineResult
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def test_build_repository_claim_pipeline_none_quarantines_not_raises(
    tmp_path: Path,
    monkeypatch,
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
            "source": {"paper": "workflow_claim_pipeline"},
            "claims": [
                {
                    "id": "valid_claim",
                    "type": "observation",
                    "context": {"id": "ctx_test"},
                    "statement": "Fundamental frequency was observed.",
                    "concepts": [concept_payload["artifact_id"]],
                    "provenance": {"paper": "workflow_claim_pipeline", "page": 1},
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
            "claims/workflow_claim_pipeline.yaml": yaml.dump(
                claim_payload,
                sort_keys=False,
            ).encode(),
        },
        "seed compiler workflow claim pipeline quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    def fail_claim_pipeline(_authored):
        return PipelineResult(
            family=PropstoreFamily.CLAIMS,
            stage=ClaimStage.CHECKED,
            output=None,
            diagnostics=(
                PassDiagnostic(
                    level="error",
                    code="claim.compile.failed",
                    message="claim pipeline returned no checked bundle",
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.CHECKED,
                    filename="workflow_claim_pipeline",
                    artifact_id="ps:claim:pipeline-none",
                    pass_name="claim.compile",
                ),
            ),
        )

    monkeypatch.setattr("propstore.compiler.workflows.run_claim_pipeline", fail_claim_pipeline)

    report = build_repository(repo, output=str(sidecar_path), force=True)

    assert report.rebuilt is True
    assert sidecar_path.exists()

    conn = sqlite3.connect(sidecar_path)
    try:
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'claim_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert diagnostic_rows == [
        (
            "claim",
            "ps:claim:pipeline-none",
            "claim_validation",
            "error",
            1,
            (
                "workflow_claim_pipeline: ps:claim:pipeline-none: "
                "claim pipeline returned no checked bundle"
            ),
        )
    ]
