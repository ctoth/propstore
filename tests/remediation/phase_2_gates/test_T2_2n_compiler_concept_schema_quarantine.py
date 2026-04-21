from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def test_build_repository_concept_schema_error_quarantines_not_raises(
    tmp_path: Path,
) -> None:
    valid_concept = normalize_concept_payloads(
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
                valid_concept,
                sort_keys=False,
            ).encode(),
            "concepts/zz_bad_schema.yaml": yaml.dump(
                {
                    "ontology_reference": {"uri": "tag:test,2026:bad-concept"},
                    "lexical_entry": {
                        "identifier": "zz_bad_schema",
                        "canonical_form": {
                            "written_rep": "Bad schema",
                            "language": "en",
                        },
                        "physical_dimension_form": "frequency",
                        "senses": [
                            {
                                "reference": {
                                    "uri": "tag:test,2026:bad-concept",
                                }
                            }
                        ],
                    },
                },
                sort_keys=False,
            ).encode(),
        },
        "seed compiler workflow concept schema quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    report = build_repository(repo, output=str(sidecar_path), force=True)

    assert report.rebuilt is True
    assert sidecar_path.exists()

    conn = sqlite3.connect(sidecar_path)
    try:
        concept_rows = conn.execute(
            "SELECT canonical_name FROM concept WHERE canonical_name = 'fundamental_frequency'"
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'concept_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert concept_rows == [("fundamental_frequency",)]
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "concept",
        "zz_bad_schema",
        "concept_validation",
        "error",
        1,
    )
    assert "missing required field `status`" in diagnostic_rows[0][5]
