"""Branch-local structured projection into merge summaries (Phase 6c).

Re-parameterized off the reference's ``RepositorySnapshot`` fixtures to plain
``MergeClaim`` + stance-dict inputs; the store-reading half lands in Phase 9.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.stances import StanceType
from propstore.aspic_bridge.translate import StanceInput
from propstore.merge.structured_merge import (
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from tests.merge_helpers import obs_claim


def _rebuts(source: str, target: str) -> StanceInput:
    return StanceInput(
        claim_id=source, target_claim_id=target, stance_type=StanceType.REBUTS
    )


def test_branch_structured_summary_reads_branch_stances() -> None:
    claims = [
        obs_claim("claim_a", "A", ["concept_x"]),
        obs_claim("claim_b", "B", ["concept_x"]),
    ]
    summary = build_branch_structured_summary(
        "master", claims, [_rebuts("claim_a", "claim_b")]
    )

    assert not hasattr(summary, "claim_ids")
    assert len(summary.assertion_ids) == 2
    assert all(a.startswith("ps:assertion:") for a in summary.assertion_ids)
    assert summary.claim_provenance["claim_a"]["paper"] == "test_paper"
    assert summary.claim_provenance["claim_b"]["paper"] == "test_paper"
    assert summary.relation_surface == {
        "attack": "preserved_via_projection",
        "non_attack": "not_preserved_in_summary",
        "ignorance": "not_preserved_in_summary",
    }
    assert summary.lossiness == (
        "subargument_identity",
        "justification_identity",
        "preference_metadata",
        "support_metadata",
        "known_non_attack_relations",
        "ignorance_relations",
    )

    claim_attack_pairs = {
        (
            summary.projection.argument_to_claim_id[attacker],
            summary.projection.argument_to_claim_id[target],
        )
        for attacker, target in (summary.projection.framework.attacks or frozenset())
    }
    assert ("claim_a", "claim_b") in claim_attack_pairs


def test_structured_merge_candidates_reuse_identical_branch_summaries() -> None:
    claims = [
        obs_claim("claim_a", "A", ["concept_x"]),
        obs_claim("claim_b", "B", ["concept_x"]),
    ]
    stances = [_rebuts("claim_a", "claim_b")]
    claim_sets = {"master": claims, "paper/structured": claims}
    stance_sets = {"master": stances, "paper/structured": stances}

    summary = build_branch_structured_summary("master", claims, stances)
    branch_summary = build_branch_structured_summary(
        "paper/structured", claims, stances
    )
    candidates = build_structured_merge_candidates(
        claim_sets,
        "master",
        "paper/structured",
        operator="sum",
        stance_sets_per_branch=stance_sets,
    )

    assert summary.content_signature == branch_summary.content_signature
    assert candidates == [summary.projection.framework]


def test_branch_structured_summary_is_stable_on_repeated_builds() -> None:
    claims = [
        obs_claim("claim_a", "A", ["concept_x"]),
        obs_claim("claim_b", "B", ["concept_x"]),
    ]
    stances = [_rebuts("claim_a", "claim_b")]

    left = build_branch_structured_summary("master", claims, stances)
    right = build_branch_structured_summary("master", claims, stances)

    assert left.assertion_ids == right.assertion_ids
    assert left.claim_provenance == right.claim_provenance
    assert left.content_signature == right.content_signature
    assert left.projection.framework == right.projection.framework


def test_branch_structured_summary_stays_local_to_branch_scope() -> None:
    summary = build_branch_structured_summary(
        "master", [obs_claim("claim_a", "A", ["concept_x"])]
    )

    assert len(summary.assertion_ids) == 1
    assert summary.assertion_ids[0].startswith("ps:assertion:")
    assert set(summary.projection.argument_to_claim_id.values()) == {"claim_a"}
    assert summary.projection.framework.attacks == frozenset()


def test_branch_structured_summary_explicitly_marks_lossy_relation_boundary() -> None:
    claims = [
        obs_claim("claim_a", "A", ["concept_x"]),
        obs_claim("claim_b", "B", ["concept_x"]),
    ]
    summary = build_branch_structured_summary("master", claims)

    assert summary.relation_surface["attack"] == "preserved_via_projection"
    assert summary.relation_surface["non_attack"] == "not_preserved_in_summary"
    assert summary.relation_surface["ignorance"] == "not_preserved_in_summary"
    assert "known_non_attack_relations" in summary.lossiness
    assert "ignorance_relations" in summary.lossiness


@settings(deadline=None)
@pytest.mark.property
@given(
    extra_targets=st.lists(
        st.from_regex(r"claim_extra_[a-z]{1,3}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    )
)
def test_branch_structured_summary_ignores_out_of_scope_stances_in_identity(
    extra_targets: list[str],
) -> None:
    claims = [
        obs_claim("claim_a", "A", ["concept_x"]),
        obs_claim("claim_b", "B", ["concept_x"]),
    ]
    in_scope = [_rebuts("claim_a", "claim_b")]
    out_of_scope = [_rebuts("claim_a", target) for target in extra_targets]

    left_summary = build_branch_structured_summary("master", claims, in_scope)
    right_summary = build_branch_structured_summary(
        "paper/x", claims, in_scope + out_of_scope
    )

    assert left_summary.assertion_ids == right_summary.assertion_ids
    assert left_summary.claim_provenance == right_summary.claim_provenance
    assert left_summary.content_signature == right_summary.content_signature
    assert left_summary.stance_rows == right_summary.stance_rows
    assert left_summary.projection.framework == right_summary.projection.framework


@settings(deadline=None)
@pytest.mark.property
@given(
    claim_order=st.permutations(("claim_a", "claim_b", "claim_c")),
    stance_order=st.permutations(("claim_b", "claim_c")),
)
def test_branch_structured_summary_is_order_invariant(
    claim_order: tuple[str, ...],
    stance_order: tuple[str, ...],
) -> None:
    claims_by_id = {
        "claim_a": obs_claim("claim_a", "A", ["concept_x"]),
        "claim_b": obs_claim("claim_b", "B", ["concept_x"]),
        "claim_c": obs_claim("claim_c", "C", ["concept_x"]),
    }
    left = build_branch_structured_summary(
        "master",
        [claims_by_id[claim_id] for claim_id in claim_order],
        [_rebuts("claim_a", target) for target in stance_order],
    )
    right = build_branch_structured_summary(
        "paper/x",
        [claims_by_id["claim_c"], claims_by_id["claim_a"], claims_by_id["claim_b"]],
        [_rebuts("claim_a", "claim_c"), _rebuts("claim_a", "claim_b")],
    )

    assert left.assertion_ids == right.assertion_ids
    assert left.claim_provenance == right.claim_provenance
    assert left.content_signature == right.content_signature
    assert left.stance_rows == right.stance_rows
    assert left.projection.framework == right.projection.framework
