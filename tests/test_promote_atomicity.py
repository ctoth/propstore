from __future__ import annotations

import sqlite3
from pathlib import Path

from propstore.source import finalize_source_branch, promote_source_branch, source_branch_name
from propstore.source.promote import PromotionResult

from tests.family_helpers import build_sidecar
from tests.test_source_promotion_alignment import _setup_source_with_partial_validity


def test_promote_returns_in_memory_blocked_diagnostics_after_committed_mirror(
    tmp_path: Path,
) -> None:
    source_name = "ws_c_partial"
    repo = _setup_source_with_partial_validity(tmp_path, source_name=source_name)
    finalize_source_branch(repo, source_name)
    build_sidecar(repo, repo.sidecar_path, force=True, commit_hash=repo.snapshot.head_sha())

    result = promote_source_branch(repo, source_name)

    assert isinstance(result, PromotionResult)
    assert result.commit_sha
    assert result.sidecar_mirror_ok is True
    assert result.sidecar_mirror_error is None
    assert result.blocked_claims
    assert result.blocked_diagnostics
    blocked_ids = {claim.artifact_id for claim in result.blocked_claims}
    assert set(result.blocked_diagnostics).issubset(blocked_ids)
    assert any(
        "stance target" in detail
        for diagnostics in result.blocked_diagnostics.values()
        for _, detail in diagnostics
    )

    conn = sqlite3.connect(repo.sidecar_path)
    try:
        mirrored_rows = conn.execute(
            "SELECT id FROM claim_core WHERE branch = ? AND promotion_status = 'blocked'",
            (source_branch_name(source_name),),
        ).fetchall()
    finally:
        conn.close()
    assert {row[0] for row in mirrored_rows} == blocked_ids
