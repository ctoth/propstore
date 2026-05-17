from __future__ import annotations

from propstore.repository import Repository
from quire.derived_runtime import connect_sqlite_store
from propstore.families.registry import SOURCE_BRANCH, SourceRef
from propstore.source.status import inspect_source_status
from tests.family_helpers import materialized_world_store


def test_source_status_escapes_underscore_in_branch_like_pattern(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    target_branch = SOURCE_BRANCH.branch_name(repo, SourceRef("foo_bar"))
    alien_branch = target_branch.replace("_", "x")
    assert alien_branch != target_branch

    handle = materialized_world_store(repo, force=True)
    conn = connect_sqlite_store(handle.path)
    try:
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

    report = inspect_source_status(handle, "foo_bar")

    assert len(report.rows) == 1
    assert report.rows[0].claim_id == "claim-1"
    assert report.rows[0].diagnostics == ()
