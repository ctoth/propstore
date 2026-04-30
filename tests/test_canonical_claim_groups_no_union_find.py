from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage import init_git_store
from tests.ws_l_merge_helpers import (
    claim_yaml_with_explicit_identities,
    obs_claim,
    snapshot,
)


def test_logical_id_alias_chain_does_not_union_without_accepted_sameas(tmp_path) -> None:
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)

    claim_a = obs_claim("a", "A", ["concept_a"], paper="paper_a")
    claim_a["artifact_id"] = "ps:claim:sameasa000000000001"
    claim_a["logical_ids"] = [
        {"namespace": "paper_a", "value": "a"},
        {"namespace": "shared", "value": "ab"},
    ]
    claim_b = obs_claim("b", "B", ["concept_b"], paper="paper_b")
    claim_b["artifact_id"] = "ps:claim:sameasb000000000001"
    claim_b["logical_ids"] = [
        {"namespace": "paper_b", "value": "b"},
        {"namespace": "shared", "value": "ab"},
        {"namespace": "shared", "value": "bc"},
    ]
    claim_c = obs_claim("c", "C", ["concept_c"], paper="paper_c")
    claim_c["artifact_id"] = "ps:claim:sameasc000000000001"
    claim_c["logical_ids"] = [
        {"namespace": "paper_c", "value": "c"},
        {"namespace": "shared", "value": "bc"},
    ]

    kr.commit_files(
        {"claims/a.yaml": claim_yaml_with_explicit_identities([claim_a], paper="paper_a")},
        "left",
    )
    kr.commit_files(
        {
            "claims/bc.yaml": claim_yaml_with_explicit_identities(
                [claim_b, claim_c],
                paper="paper_b",
            )
        },
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 3
    assert len({argument.canonical_claim_id for argument in merge.arguments}) == 3
    assert {
        argument.canonical_claim_id
        for argument in merge.arguments
    } == {"paper_a:a", "paper_b:b", "paper_c:c"}
