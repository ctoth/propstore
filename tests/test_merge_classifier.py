"""Repository merge-framework math over plain per-branch claim sets.

Re-parameterized off the reference's ``RepositorySnapshot`` fixtures to plain
``MergeClaim`` inputs (Phase 6c). The tests that exercised the two-parent storage
commit (``create_merge_commit``) and the ``Repository`` facade are deferred to
Phase 9 and skipped below with a reason.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.merge import IntegrityConstraint, IntegrityConstraintViolation
from propstore.merge.merge_classifier import build_merge_framework
from tests.merge_helpers import obs_claim, param_claim


def test_identical_claims_collapse_to_one_emitted_argument() -> None:
    claim = obs_claim("claim1", "Base", ["concept_x"])
    merge = build_merge_framework(
        {"master": [claim], "paper/test": [claim]},
        "master",
        "paper/test",
    )

    assert len(merge.arguments) == 1
    assert merge.arguments[0].assertion_id.startswith("ps:assertion:")
    assert merge.arguments[0].canonical_claim_id == "claim1"
    assert merge.arguments[0].branch_origins == ("master", "paper/test")


def test_syntax_independence_claim_order() -> None:
    claim_a = obs_claim("claimA", "A", ["concept_a"])
    claim_b = obs_claim("claimB", "B", ["concept_b"])

    merge = build_merge_framework(
        {"master": [claim_a, claim_b], "paper/reorder": [claim_b, claim_a]},
        "master",
        "paper/reorder",
    )

    emitted = {argument.canonical_claim_id for argument in merge.arguments}
    assert emitted == {"claimA", "claimB"}
    assert {argument.assertion_id for argument in merge.arguments} == set(
        merge.framework.arguments
    )


def test_single_branch_addition_emits_one_argument() -> None:
    claim = obs_claim("claimA", "Observation A", ["concept_a"])
    merge = build_merge_framework(
        {"master": [claim], "paper/rename": []},
        "master",
        "paper/rename",
    )

    assert len(merge.arguments) == 1
    assert merge.arguments[0].assertion_id.startswith("ps:assertion:")
    assert merge.arguments[0].canonical_claim_id == "claimA"
    assert merge.arguments[0].branch_origins == ("master",)


def test_conflict_emits_symmetric_attacks() -> None:
    base = [param_claim("claim1", "concept_x", 250.0)]
    merge = build_merge_framework(
        {
            "master": [param_claim("claim1", "concept_x", 300.0)],
            "paper/conflict": [param_claim("claim1", "concept_x", 150.0)],
        },
        "master",
        "paper/conflict",
        base_claims=base,
    )

    assert len(merge.arguments) == 2
    left_id, right_id = sorted(argument.assertion_id for argument in merge.arguments)
    assert (left_id, right_id) in merge.framework.attacks
    assert (right_id, left_id) in merge.framework.attacks
    assert not merge.framework.ignorance


def test_merge_is_deterministic() -> None:
    branches = {
        "master": [param_claim("claim1", "concept_x", 300.0)],
        "paper/conflict": [param_claim("claim1", "concept_x", 150.0)],
    }
    base = [param_claim("claim1", "concept_x", 250.0)]

    merge_a = build_merge_framework(branches, "master", "paper/conflict", base_claims=base)
    merge_b = build_merge_framework(branches, "master", "paper/conflict", base_claims=base)

    assert merge_a.framework == merge_b.framework
    assert [argument.assertion_id for argument in merge_a.arguments] == [
        argument.assertion_id for argument in merge_b.arguments
    ]


def test_branch_origin_provenance_recorded_on_each_argument() -> None:
    base = [param_claim("claim1", "concept_x", 250.0)]
    merge = build_merge_framework(
        {
            "master": [param_claim("claim1", "concept_x", 300.0)],
            "paper/conflict": [param_claim("claim1", "concept_x", 150.0)],
        },
        "master",
        "paper/conflict",
        base_claims=base,
    )

    for argument in merge.arguments:
        branch_origin = argument.claim.provenance_mapping().get("branch_origin")
        assert branch_origin in argument.branch_origins


def test_integrity_constraint_filters_forbidden_artifacts() -> None:
    merge = build_merge_framework(
        {
            "master": [obs_claim("claimA", "A", ["concept_a"])],
            "paper/x": [obs_claim("claimB", "B", ["concept_b"])],
        },
        "master",
        "paper/x",
        integrity_constraint=IntegrityConstraint(forbidden_artifact_ids=frozenset({"claimB"})),
    )

    assert {argument.artifact_id for argument in merge.arguments} == {"claimA"}


def test_integrity_constraint_requires_present_artifacts() -> None:
    with pytest.raises(IntegrityConstraintViolation):
        build_merge_framework(
            {
                "master": [obs_claim("claimA", "A", ["concept_a"])],
                "paper/x": [],
            },
            "master",
            "paper/x",
            integrity_constraint=IntegrityConstraint(
                required_artifact_ids=frozenset({"missing"})
            ),
        )


@settings(deadline=None)
@pytest.mark.property
@given(
    left_ids=st.lists(
        st.from_regex(r"left_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
    right_ids=st.lists(
        st.from_regex(r"right_[a-z]{1,4}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
)
def test_merge_emits_exact_union_of_disjoint_branch_additions(
    left_ids: list[str],
    right_ids: list[str],
) -> None:
    assume(set(left_ids).isdisjoint(right_ids))

    branches = {
        "master": [obs_claim(cid, f"{cid} statement", [f"concept_{cid}"]) for cid in left_ids],
        "paper/p": [obs_claim(cid, f"{cid} statement", [f"concept_{cid}"]) for cid in right_ids],
    }
    merge = build_merge_framework(branches, "master", "paper/p")

    merged_artifact_ids = {argument.artifact_id for argument in merge.arguments}
    assert merged_artifact_ids == set(left_ids) | set(right_ids)
