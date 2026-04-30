from __future__ import annotations

import pytest

from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from propstore.storage import init_git_store
from tests.ws_l_merge_helpers import claim_yaml, obs_claim, snapshot


def test_non_claim_file_conflict_is_surfaced_symmetrically(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {
            "claims/base.yaml": claim_yaml([obs_claim("base", "Base", ["concept_base"])]),
            "concepts/shared.yaml": b"name: base\n",
        },
        "seed",
    )
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files({"concepts/shared.yaml": b"name: left\n"}, "left")
    kr.commit_files(
        {"concepts/shared.yaml": b"name: right\n"},
        "right",
        branch=branch_name,
    )

    with pytest.raises(NonClaimMergeConflict) as left_first:
        create_merge_commit(snapshot(kr), "master", branch_name)
    with pytest.raises(NonClaimMergeConflict) as right_first:
        create_merge_commit(snapshot(kr), branch_name, "master")

    assert left_first.value.path == "concepts/shared.yaml"
    assert right_first.value.path == "concepts/shared.yaml"
    assert left_first.value.left_sha != left_first.value.right_sha
    assert right_first.value.left_sha != right_first.value.right_sha
