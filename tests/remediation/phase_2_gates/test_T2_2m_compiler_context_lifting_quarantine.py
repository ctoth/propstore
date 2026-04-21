from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def test_build_repository_context_lifting_error_quarantines_not_raises(
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
            "contexts/ctx_root.yaml": yaml.dump(
                {
                    "id": "ctx_root",
                    "name": "Root",
                    "lifting_rules": [
                        {
                            "id": "lift_missing_target",
                            "source": "ctx_root",
                            "target": "ctx_missing",
                        },
                    ],
                },
                sort_keys=False,
            ).encode(),
        },
        "seed compiler workflow context lifting quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    report = build_repository(repo, output=str(sidecar_path), force=True)

    assert report.rebuilt is True
    assert sidecar_path.exists()

    conn = sqlite3.connect(sidecar_path)
    try:
        context_rows = conn.execute(
            "SELECT id FROM context WHERE id = 'ctx_root'"
        ).fetchall()
        lifting_rows = conn.execute(
            "SELECT id FROM context_lifting_rule WHERE id = 'lift_missing_target'"
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

    assert context_rows == [("ctx_root",)]
    assert lifting_rows == []
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "context",
        "ctx_root",
        "context_validation",
        "error",
        1,
    )
    assert "nonexistent target context" in diagnostic_rows[0][5]
