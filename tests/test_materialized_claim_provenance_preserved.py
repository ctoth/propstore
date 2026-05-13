from __future__ import annotations

import yaml

from propstore.claims import claim_file_claims
from propstore.merge.merge_commit import create_merge_commit
from tests.git_store_helpers import init_store
from tests.family_helpers import load_claim_files
from tests.ws_l_merge_helpers import claim_payloads, param_claim, snapshot


def test_rival_materialized_claims_keep_artifact_id_and_full_provenance(tmp_path) -> None:
    kr = init_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        claim_payloads(
            kr,
            [param_claim("claim1", "concept_x", 300.0, paper="left_paper")],
            paper="left_paper",
        ),
        "left",
    )
    kr.commit_files(
        claim_payloads(
            kr,
            [param_claim("claim1", "concept_x", 150.0, paper="right_paper")],
            paper="right_paper",
        ),
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(snapshot(kr), "master", branch_name)

    manifest = yaml.safe_load((kr.tree(commit=merge_sha) / "merge" / "manifest.yaml").read_text())
    canonical_artifact_ids = {row["artifact_id"] for row in manifest["merge"]["arguments"]}
    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    materialized = [
        claim.to_payload()
        for claim_file in claim_files
        for claim in claim_file_claims(claim_file)
        if claim.artifact_id in canonical_artifact_ids
    ]
    materialized_sources = {
        claim["source"]["paper"]
        for claim in materialized
    }

    assert {claim["artifact_id"] for claim in materialized} == canonical_artifact_ids
    assert materialized_sources == {"left_paper", "right_paper"}
    assert {claim["provenance"]["paper"] for claim in materialized} == {"left_paper", "right_paper"}
    assert {claim["provenance"]["branch_origin"] for claim in materialized} == {"master", branch_name}
