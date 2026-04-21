from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def test_build_repository_context_schema_error_quarantines_not_raises(
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
            "contexts/ctx_missing_name.yaml": yaml.dump(
                {"id": "ctx_missing_name"},
                sort_keys=False,
            ).encode(),
        },
        "seed compiler workflow context validation quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    report = build_repository(repo, output=str(sidecar_path), force=True)

    assert report.rebuilt is True
    assert sidecar_path.exists()

    conn = sqlite3.connect(sidecar_path)
    try:
        context_rows = conn.execute(
            "SELECT id FROM context WHERE id = 'ctx_missing_name'"
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'context_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert context_rows == []
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "context",
        "ctx_missing_name.yaml",
        "context_validation",
        "error",
        1,
    )
    assert "missing required field `name`" in diagnostic_rows[0][5]
