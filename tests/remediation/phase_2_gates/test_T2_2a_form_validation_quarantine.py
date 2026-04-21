from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar


def test_invalid_form_quarantines_not_raises(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "forms/frequency.yaml": yaml.dump(
                {"name": "frequency", "dimensionless": False},
                sort_keys=False,
            ).encode(),
            "forms/bogus.yaml": yaml.dump(
                {"name": "not_bogus", "dimensionless": True},
                sort_keys=False,
            ).encode(),
        },
        "seed invalid form quarantine test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        form_rows = conn.execute(
            "SELECT name FROM form WHERE name = 'frequency'"
        ).fetchall()
        diagnostic_rows = conn.execute(
            """
            SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'form_validation'
            """
        ).fetchall()
    finally:
        conn.close()

    assert form_rows == [("frequency",)]
    assert diagnostic_rows
    assert diagnostic_rows[0][:5] == ("form", "bogus", "form_validation", "error", 1)
    assert "does not match filename" in diagnostic_rows[0][5]
