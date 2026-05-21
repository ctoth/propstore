from __future__ import annotations

from sqlalchemy import text

from propstore.families.world_charters import world_sqlalchemy_schema
from propstore.repository import Repository
from propstore.families.registry import SOURCE_BRANCH, SourceRef
from propstore.source.status import inspect_source_status
from quire.sqlalchemy_store import writable_session
from tests.family_helpers import materialized_world_store


def test_source_status_escapes_underscore_in_branch_like_pattern(tmp_path):
    repo = Repository.init(tmp_path / "knowledge")
    target_branch = SOURCE_BRANCH.branch_name(repo, SourceRef("foo_bar"))
    alien_branch = target_branch.replace("_", "x")
    assert alien_branch != target_branch

    handle = materialized_world_store(repo, force=True)
    schema = world_sqlalchemy_schema()
    with writable_session(handle.path, schema) as derived:
        derived.session.execute(
            text(
                """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, source_paper, provenance_page,
                premise_kind, branch, build_status, promotion_status
            ) VALUES (
                :claim_id, :primary_logical_id, :logical_ids_json, :version_id,
                :content_hash, :seq, :type, :source_paper, :provenance_page,
                :premise_kind, :branch, :build_status, :promotion_status
            )
            """,
            ),
            {
                "claim_id": "claim-1",
                "primary_logical_id": "",
                "logical_ids_json": "[]",
                "version_id": "",
                "content_hash": "",
                "seq": 0,
                "type": "promotion_blocked",
                "source_paper": "paper-a",
                "provenance_page": 0,
                "premise_kind": "ordinary",
                "branch": target_branch,
                "build_status": "ingested",
                "promotion_status": "blocked",
            },
        )
        derived.session.execute(
            text(
                """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (
                :claim_id, :source_kind, :source_ref, :diagnostic_kind,
                :severity, :blocking, :message, :file, :detail_json
            )
            """,
            ),
            {
                "claim_id": None,
                "source_kind": "claim",
                "source_ref": f"{alien_branch}:claim-1",
                "diagnostic_kind": "promotion_blocked",
                "severity": "error",
                "blocking": 1,
                "message": "alien branch diagnostic",
                "file": None,
                "detail_json": None,
            },
        )
        derived.session.commit()

    report = inspect_source_status(handle, "foo_bar")

    assert len(report.rows) == 1
    assert report.rows[0].claim_id == "claim-1"
    assert report.rows[0].diagnostics == ()
