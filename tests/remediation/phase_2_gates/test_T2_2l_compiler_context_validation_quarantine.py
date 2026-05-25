from __future__ import annotations

from pathlib import Path

from quire.sqlalchemy_store import readonly_session
from sqlalchemy import text
import yaml

from propstore.compiler.workflows import build_repository
from propstore.families.registry import world_schema
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
    report = build_repository(repo, force=True)

    assert report.rebuilt is True
    assert report.derived_store is not None
    sidecar_path = Path(report.derived_store.path)
    assert sidecar_path.exists()

    with readonly_session(sidecar_path, world_schema()) as derived:
        context_ids = {
            str(row[0])
            for row in derived.session.execute(text("SELECT id FROM context")).fetchall()
        }
        diagnostic_rows = derived.session.execute(
            text(
                """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'context_validation'
            """
            )
        ).fetchall()

    assert "ctx_missing_name" not in context_ids
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == (
        "context",
        "ctx_missing_name",
        "context_validation",
        "error",
        1,
    )
    assert "missing required field `name`" in diagnostic_rows[0][5]
