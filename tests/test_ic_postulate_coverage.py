from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from propstore.families.identity.claims import derive_claim_artifact_id
from propstore.merge.merge_classifier import IntegrityConstraint, build_merge_framework
from propstore.storage import init_git_store
from tests.ws_l_merge_helpers import claim_yaml, obs_claim, snapshot


def test_integrity_constraint_prunes_forbidden_artifact_ids(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": claim_yaml([obs_claim("left", "Left", ["concept_left"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": claim_yaml([obs_claim("right", "Right", ["concept_right"])])},
        "right",
        branch=branch_name,
    )

    forbidden = derive_claim_artifact_id("test_paper", "right")
    merge = build_merge_framework(
        snapshot(kr),
        "master",
        branch_name,
        integrity_constraint=IntegrityConstraint(forbidden_artifact_ids=frozenset({forbidden})),
    )

    assert {argument.artifact_id for argument in merge.arguments} == {
        derive_claim_artifact_id("test_paper", "left")
    }


@given(
    left_name=st.from_regex(r"left_[a-z]{1,3}", fullmatch=True),
    right_name=st.from_regex(r"right_[a-z]{1,3}", fullmatch=True),
    third_name=st.from_regex(r"third_[a-z]{1,3}", fullmatch=True),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.property
def test_nary_merge_profile_preserves_disjoint_branch_additions(
    left_name: str,
    right_name: str,
    third_name: str,
) -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "knowledge"
        kr = init_git_store(root)
        base_sha = kr.commit_files({}, "seed")
        right_branch = "paper/right"
        third_branch = "paper/third"
        kr.create_branch(right_branch, source_commit=base_sha)
        kr.create_branch(third_branch, source_commit=base_sha)
        kr.commit_files(
            {"claims/left.yaml": claim_yaml([obs_claim(left_name, "Left", ["concept_left"])])},
            "left",
        )
        kr.commit_files(
            {"claims/right.yaml": claim_yaml([obs_claim(right_name, "Right", ["concept_right"])])},
            "right",
            branch=right_branch,
        )
        kr.commit_files(
            {"claims/third.yaml": claim_yaml([obs_claim(third_name, "Third", ["concept_third"])])},
            "third",
            branch=third_branch,
        )

        merge = build_merge_framework(
            snapshot(kr),
            "master",
            right_branch,
            additional_branches=(third_branch,),
        )

        assert {argument.artifact_id for argument in merge.arguments} == {
            derive_claim_artifact_id("test_paper", left_name),
            derive_claim_artifact_id("test_paper", right_name),
            derive_claim_artifact_id("test_paper", third_name),
        }
