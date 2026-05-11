from __future__ import annotations

import sqlite3
from pathlib import Path

from propstore.families.claims.stages import ClaimStage
from propstore.families.registry import PropstoreFamily
from propstore.repository import Repository
from propstore.semantic_passes.types import PassDiagnostic, PipelineResult
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload
from tests.family_helpers import claim_artifact_commit_payloads


def test_claim_pipeline_none_quarantines_not_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    claim_payload = normalize_claims_payload(
        {
            "source": {"paper": "bad_claims"},
            "claims": [
                {
                    "id": "bad",
                    "type": "observation",
                    "context": {"id": "ctx_test"},
                    "statement": "Claim pipeline should quarantine this artifact.",
                    "provenance": {"paper": "bad_claims", "page": 1},
                }
            ],
        }
    )
    repo.git.commit_files(
        claim_artifact_commit_payloads(
            repo,
            claim_payload,
            source="claims/bad_claims.yaml",
        ),
        "seed claim pipeline quarantine test",
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
                    filename="bad_claims",
                    artifact_id="ps:claim:bad",
                    pass_name="claim.compile",
                ),
            ),
        )

    monkeypatch.setattr("propstore.sidecar.build.run_claim_pipeline", fail_claim_pipeline)

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        diagnostic_rows = conn.execute(
            """
            SELECT claim_id, source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'claim_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert diagnostic_rows == [
        (
            "ps:claim:bad",
            "claim",
            "ps:claim:bad",
            "claim_validation",
            "error",
            1,
            "bad_claims: ps:claim:bad: claim pipeline returned no checked bundle",
        )
    ]
