from __future__ import annotations

from types import SimpleNamespace

from propstore.sidecar.schema import create_claim_tables, create_context_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.promote import _write_promotion_blocked_sidecar_rows


def test_promotion_blocked_diagnostic_delete_is_scoped_to_source_branch(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_context_tables(conn)
        create_claim_tables(conn)
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "claim-1",
                "claim",
                "source/a:claim-1",
                "promotion_blocked",
                "error",
                1,
                "stale branch a",
                None,
                '{"source_branch": "source/a"}',
            ),
        )
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "claim-1",
                "claim",
                "source/b:claim-1",
                "promotion_blocked",
                "error",
                1,
                "keep branch b",
                None,
                '{"source_branch": "source/b"}',
            ),
        )
        conn.commit()
    finally:
        conn.close()

    claim = SimpleNamespace(artifact_id="claim-1", id="local-claim")
    _write_promotion_blocked_sidecar_rows(
        sidecar_path,
        "source/a",
        "paper-a",
        [claim],
        {"claim-1": [("concept_mapping", "fresh branch a")]},
    )

    conn = connect_sidecar(sidecar_path)
    try:
        rows = conn.execute(
            """
            SELECT source_ref, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'promotion_blocked'
            ORDER BY source_ref, message
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("source/a:claim-1", "fresh branch a"),
        ("source/b:claim-1", "keep branch b"),
    ]
