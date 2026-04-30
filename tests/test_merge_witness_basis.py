from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage import init_git_store
from tests.ws_l_merge_helpers import claim_yaml, obs_claim, snapshot


def test_every_merge_argument_has_source_artifact_witness_basis(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": claim_yaml([obs_claim("left", "Left", ["concept_left"], paper="left_paper")], paper="left_paper")},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": claim_yaml([obs_claim("right", "Right", ["concept_right"], paper="right_paper")], paper="right_paper")},
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(snapshot(kr), "master", branch_name)

    assert merge.arguments
    for argument in merge.arguments:
        assert argument.witness_basis
        assert argument.witness_basis[0].source_artifact_id == argument.artifact_id
        assert argument.witness_basis[0].source_paper in {"left_paper", "right_paper"}
