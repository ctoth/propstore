from __future__ import annotations

import yaml

from propstore.claims import claim_file_payload
from propstore.merge.merge_commit import create_merge_commit
from propstore.storage import init_git_store
from tests.family_helpers import load_claim_files
from tests.ws_l_merge_helpers import (
    claim_yaml_with_explicit_identities,
    obs_claim,
    snapshot,
)


def test_cross_paper_corroboration_survives_merge_materialization(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)

    left_claim = obs_claim(
        "claim_a",
        "The same proposition",
        ["concept_x"],
        paper="left_paper",
    )
    left_claim["artifact_id"] = "ps:claim:leftcorroborates0001"
    left_claim["logical_ids"] = [{"namespace": "left_paper", "value": "claim_a"}]
    right_claim = obs_claim(
        "claim_b",
        "The same proposition",
        ["concept_x"],
        paper="right_paper",
    )
    right_claim["artifact_id"] = "ps:claim:rightcorroborates0001"
    right_claim["logical_ids"] = [{"namespace": "right_paper", "value": "claim_b"}]

    kr.commit_files(
        {"claims/left.yaml": claim_yaml_with_explicit_identities([left_claim], paper="left_paper")},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": claim_yaml_with_explicit_identities([right_claim], paper="right_paper")},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(snapshot(kr), "master", branch_name)

    manifest = yaml.safe_load((kr.tree(commit=merge_sha) / "merge" / "manifest.yaml").read_text())
    arguments = manifest["merge"]["arguments"]
    assert len(arguments) == 2
    assert {row["artifact_id"] for row in arguments} == {
        "ps:claim:leftcorroborates0001",
        "ps:claim:rightcorroborates0001",
    }
    assert all(row["witness_basis"] for row in arguments)

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    materialized_papers = {
        claim["provenance"]["paper"]
        for claim_file in claim_files
        for claim in claim_file_payload(claim_file).get("claims", [])
    }
    assert materialized_papers == {"left_paper", "right_paper"}
