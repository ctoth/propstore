from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from quire.git_store import HeadMismatchError

from propstore.source import finalize_source_branch, promote_source_branch
from tests.family_helpers import materialized_world_store_path
from tests.test_source_promotion_alignment import _setup_source_with_partial_validity


def test_promote_cas_rejection_does_not_write_blocked_sidecar_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_name = "mixed"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    sidecar_path = materialized_world_store_path(
        repo,
        force=True,
        commit_hash=repo.git.head_sha(),
    )
    expected_head = repo.git.branch_sha("master")
    original_commit_batch = type(repo.git).commit_batch

    def stale_commit_batch(self, adds, deletes, message, *, branch=None, expected_head=None):
        if branch == "master" and expected_head == expected_head_at_start:
            raise HeadMismatchError(
                branch=branch,
                expected_head=expected_head,
                actual_head="concurrent-head",
            )
        return original_commit_batch(
            self,
            adds,
            deletes,
            message,
            branch=branch,
            expected_head=expected_head,
        )

    expected_head_at_start = expected_head
    monkeypatch.setattr(type(repo.git), "commit_batch", stale_commit_batch)

    with pytest.raises(HeadMismatchError):
        promote_source_branch(repo, source_name)

    conn = sqlite3.connect(sidecar_path)
    try:
        blocked_rows = conn.execute(
            "SELECT id FROM claim_core WHERE promotion_status = 'blocked'"
        ).fetchall()
        diagnostic_rows = conn.execute(
            "SELECT claim_id FROM build_diagnostics WHERE diagnostic_kind = 'promotion_blocked'"
        ).fetchall()
    finally:
        conn.close()

    assert blocked_rows == []
    assert diagnostic_rows == []
