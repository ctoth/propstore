from __future__ import annotations

import pytest
import yaml

from propstore.merge.merge_commit import create_merge_commit
from propstore.repository import Repository
from propstore.storage import init_git_store
from propstore.storage.snapshot import RepositorySnapshot
from quire.git_store import GitStore
from tests.conftest import normalize_claims_payload


def _claim_yaml(claim_id: str, statement: str) -> bytes:
    payload = normalize_claims_payload({
        "source": {
            "paper": "race-test",
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": [
            {
                "id": claim_id,
                "type": "observation",
                "statement": statement,
                "concepts": [f"concept_{claim_id}"],
                "provenance": {"paper": "race-test", "page": 1},
            }
        ],
    })
    return yaml.dump(payload, sort_keys=False).encode()


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


def test_merge_commit_rejects_target_branch_moved_before_materialization(tmp_path, monkeypatch):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({"claims/base.yaml": _claim_yaml("base", "Base")}, "seed")
    branch_name = "paper/race"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files({"claims/left.yaml": _claim_yaml("left", "Left")}, "left")
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml("right", "Right")},
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
            racing_sha = kr.commit_files({"claims/race.yaml": _claim_yaml("race", "Race")}, "race")
        return original_commit_flat_tree(*args, **kwargs)

    monkeypatch.setattr(snapshot_git, "commit_flat_tree", race_before_materialization)

    with pytest.raises(ValueError, match="head mismatch"):
        create_merge_commit(snapshot, "master", branch_name)

    assert racing_sha is not None
    assert kr.branch_sha("master") == racing_sha
