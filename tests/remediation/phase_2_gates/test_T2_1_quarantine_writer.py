from __future__ import annotations

from pathlib import Path

from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session
from propstore.families.diagnostics.declaration import quarantine_diagnostic
from propstore.families.diagnostics.declaration import BuildDiagnostic
from propstore.families.registry import world_schema


def test_quarantine_diagnostic_round_trips_through_charter(tmp_path: Path) -> None:
    schema = world_schema()
    db_path = tmp_path / "sidecar.sqlite"
    create_sqlalchemy_store(db_path, schema)

    diagnostic = quarantine_diagnostic(
        artifact_id="c-2",
        kind="claim",
        diagnostic_kind="claim_quarantine",
        message="payload is None",
    )

    with writable_session(db_path, schema) as derived:
        derived.add(diagnostic)
        derived.commit()
        row = derived.session.get(BuildDiagnostic, 1)

    assert row is not None
    assert row.source_kind == "claim"
    assert row.source_ref == "c-2"
    assert row.diagnostic_kind == "claim_quarantine"
    assert row.severity == "error"
    assert row.blocking == 1
    assert row.message == "payload is None"
