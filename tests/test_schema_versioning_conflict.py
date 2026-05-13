from __future__ import annotations

import pytest

from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from tests.git_store_helpers import init_store
from tests.ws_l_merge_helpers import claim_payloads, obs_claim, snapshot


def test_stance_family_schema_conflict_is_not_silently_left_wins(tmp_path) -> None:
    kr = init_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {
            **claim_payloads(kr, [obs_claim("base", "Base", ["concept_base"])]),
            "stances/ps__claim__base.yaml": (
                b"source_claim: ps:claim:base\n"
                b"target: ps:claim:base\n"
                b"type: supports\n"
            ),
        },
        "seed",
    )
    branch_name = "paper/right"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {
            "stances/ps__claim__base.yaml": (
                b"source_claim: ps:claim:base\nclassification_model: left\n"
                b"target: ps:claim:base\n"
                b"type: supports\n"
            )
        },
        "left",
    )
    kr.commit_files(
        {
            "stances/ps__claim__base.yaml": (
                b"source_claim: ps:claim:base\nclassification_model: right\n"
                b"target: ps:claim:base\n"
                b"type: supports\n"
            )
        },
        "right",
        branch=branch_name,
    )

    with pytest.raises(NonClaimMergeConflict) as excinfo:
        create_merge_commit(snapshot(kr), "master", branch_name)

    assert excinfo.value.path == "stances/ps__claim__base.yaml"
    assert excinfo.value.family == "stances"
