from __future__ import annotations

from propstore.repository import Repository
from propstore.sidecar.schema import create_claim_tables, create_context_tables
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.common import source_branch_name
from propstore.source.status import inspect_source_status


def test_source_status_escapes_underscore_in_branch_like_pattern(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    target_branch = source_branch_name("foo_bar")
    alien_branch = target_branch.replace("_", "x")
    assert alien_branch != target_branch

    conn = connect_sidecar(repo.sidecar_path)
    try:
        create_context_tables(conn)
        create_claim_tables(conn)
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, source_paper, provenance_page,
                premise_kind, branch, build_status, promotion_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "claim-1",
                "",
                "[]",
                "",
                "",
                0,
                "promotion_blocked",
                "paper-a",
                0,
                "ordinary",
                target_branch,
                "ingested",
                "blocked",
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
                None,
                "claim",
                f"{alien_branch}:claim-1",
                "promotion_blocked",
                "error",
                1,
                "alien branch diagnostic",
                None,
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    report = inspect_source_status(repo, "foo_bar")

    assert len(report.rows) == 1
    assert report.rows[0].claim_id == "claim-1"
    assert report.rows[0].diagnostics == ()
