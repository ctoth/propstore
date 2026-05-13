from __future__ import annotations

import pytest

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from tests.git_store_helpers import init_store
from propstore.storage.snapshot import RepositorySnapshot
from quire.git_store import GitStore, HeadMismatchError
from tests.ws_l_merge_helpers import claim_payloads


def _claim_payloads(kr: GitStore, claim_id: str, statement: str) -> dict[str, bytes]:
    return claim_payloads(
        kr,
        [
            {
                "id": claim_id,
                "type": "observation",
                "statement": statement,
                "concepts": [f"concept_{claim_id}"],
                "provenance": {"paper": "race-test", "page": 1},
            }
        ],
        paper="race-test",
    )


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


def test_merge_commit_rejects_target_branch_moved_before_materialization(tmp_path, monkeypatch):
    kr = init_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(_claim_payloads(kr, "base", "Base"), "seed")
    branch_name = "paper/race"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(_claim_payloads(kr, "left", "Left"), "left")
    kr.commit_files(
        _claim_payloads(kr, "right", "Right"),
        "right",
        branch=branch_name,
    )
    snapshot = _snapshot(kr)
    snapshot_git = snapshot.git
    racing_sha: str | None = None
    original_commit_flat_tree = snapshot_git.commit_flat_tree

    def race_before_materialization(*args: object, **kwargs: object) -> str:
        nonlocal racing_sha
        if racing_sha is None:
            racing_sha = kr.commit_files(_claim_payloads(kr, "race", "Race"), "race")
        return original_commit_flat_tree(*args, **kwargs)

    monkeypatch.setattr(snapshot_git, "commit_flat_tree", race_before_materialization)

    with pytest.raises(HeadMismatchError):
        create_merge_commit(snapshot, "master", branch_name)

    assert racing_sha is not None
    assert kr.branch_sha("master") == racing_sha
