from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage import init_git_store
from tests.ws_l_merge_helpers import claim_yaml, param_claim, snapshot


def test_regime_split_same_value_claims_remain_distinct_with_ignorance(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/regime-right"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {
            "claims/left.yaml": claim_yaml(
                [param_claim("claim1", "concept_x", 300.0, conditions=["T < 100"])],
            )
        },
        "left",
    )
    kr.commit_files(
        {
            "claims/right.yaml": claim_yaml(
                [param_claim("claim1", "concept_x", 300.0, conditions=["T >= 100"])],
            )
        },
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 2
    assert len({argument.assertion_id for argument in merge.arguments}) == 2
    left_id, right_id = sorted(argument.assertion_id for argument in merge.arguments)
    assert (left_id, right_id) in merge.framework.ignorance
    assert (right_id, left_id) in merge.framework.ignorance
    assert not merge.framework.attacks
