from __future__ import annotations

import sqlite3
from pathlib import Path

from propstore.sidecar.quarantine import QuarantinableWriter, Quarantined, Written
from propstore.sidecar.schema import create_build_diagnostics_table


def test_writer_quarantines_on_any_failure(tmp_path: Path) -> None:
    conn = sqlite3.connect(tmp_path / "sidecar.sqlite")
    create_build_diagnostics_table(conn)
    writer = QuarantinableWriter(conn)

    written = writer.try_write(artifact_id="c-1", kind="claim", payload={"ok": True})
    assert isinstance(written, Written)

    quarantined = writer.try_write(artifact_id="c-2", kind="claim", payload=None)
    assert isinstance(quarantined, Quarantined)

    rows = conn.execute(
        """
        SELECT source_kind, source_ref, diagnostic_kind, severity, blocking, message
        FROM build_diagnostics
        WHERE source_kind = 'claim' AND source_ref = 'c-2'
        """
    ).fetchall()
    assert rows == [
        ("claim", "c-2", "claim_quarantine", "error", 1, "payload is None")
    ]
