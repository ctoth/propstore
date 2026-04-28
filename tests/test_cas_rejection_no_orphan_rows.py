from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from propstore.repository import StaleHeadError
from propstore.source import finalize_source_branch, promote_source_branch
from tests.family_helpers import build_sidecar
from tests.test_source_promotion_alignment import _setup_source_with_partial_validity


def test_promote_cas_rejection_does_not_write_blocked_sidecar_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_name = "mixed"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.snapshot.head_sha())
    expected_head = repo.snapshot.branch_head("master")
    original_commit_batch = type(repo.git).commit_batch

    def stale_commit_batch(self, adds, deletes, message, *, branch=None, expected_head=None):
        if branch == "master" and expected_head == expected_head_at_start:
            raise ValueError(
                f"Branch {branch!r} head mismatch: expected {expected_head}, got concurrent-head"
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

    with pytest.raises(StaleHeadError):
        promote_source_branch(repo, source_name)

    conn = sqlite3.connect(repo.sidecar_path)
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
