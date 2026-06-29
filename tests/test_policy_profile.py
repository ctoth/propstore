from __future__ import annotations

import pytest

from propstore.policies import (
    DEFAULT_ITERATED_OPERATOR,
    AdmissibilityProfile,
    MergePolicy,
    PolicyProfile,
    RevisionPolicy,
    default_policy_profile,
    policy_profile_from_render_policy,
)
from propstore.world.types import (
    ArgumentationSemantics,
    MergeOperator,
    ReasoningBackend,
    RenderPolicy,
)


def test_default_policy_profile_id_is_content_addressed() -> None:
    profile = default_policy_profile()

    assert profile.profile_id.startswith("urn:propstore:policy-profile:")
    assert profile.profile_id.endswith(profile.content_hash)
    assert profile.revision.operator == DEFAULT_ITERATED_OPERATOR


def test_policy_profile_id_is_deterministic_for_equal_content() -> None:
    first = PolicyProfile(merge=MergePolicy(operator=MergeOperator.GMAX))
    second = PolicyProfile(merge=MergePolicy(operator=MergeOperator.GMAX))

    assert first.profile_id == second.profile_id
    assert first.content_hash == second.content_hash


def test_distinct_policy_content_yields_distinct_profile_id() -> None:
    sigma = PolicyProfile(merge=MergePolicy(operator=MergeOperator.SIGMA))
    gmax = PolicyProfile(merge=MergePolicy(operator=MergeOperator.GMAX))

    assert sigma.profile_id != gmax.profile_id


def test_to_dict_round_trips_through_from_dict() -> None:
    profile = PolicyProfile(
        revision=RevisionPolicy(operator="lexicographic", allow_reintroduction=True),
        merge=MergePolicy(operator=MergeOperator.MAX, branch_filter=("main", "rc")),
        admissibility=AdmissibilityProfile(
            semantics=ArgumentationSemantics.PREFERRED,
            reasoning_backend=ReasoningBackend.ATMS,
        ),
        label="experiment",
    )

    payload = profile.to_dict()
    restored = PolicyProfile.from_dict(payload)

    assert restored.profile_id == profile.profile_id
    assert restored.content_hash == profile.content_hash
    assert restored.to_dict() == payload
    assert restored.merge.branch_filter == ("main", "rc")


def test_from_dict_rejects_tampered_content_hash() -> None:
    payload = default_policy_profile().to_dict()
    payload["content_hash"] = "0" * 64

    with pytest.raises(ValueError, match="content_hash"):
        PolicyProfile.from_dict(payload)


def test_from_dict_rejects_tampered_profile_id() -> None:
    payload = default_policy_profile().to_dict()
    payload["profile_id"] = "urn:propstore:policy-profile:deadbeef"

    with pytest.raises(ValueError, match="profile_id"):
        PolicyProfile.from_dict(payload)


def test_policy_profile_from_render_policy_lowers_render_choices() -> None:
    policy = RenderPolicy(
        merge_operator=MergeOperator.GMAX,
        branch_filter=("main",),
        semantics=ArgumentationSemantics.PREFERRED,
        pessimism_index=0.25,
    )

    profile = policy_profile_from_render_policy(policy)

    assert profile.merge.operator == MergeOperator.GMAX
    assert profile.merge.branch_filter == ("main",)
    assert profile.admissibility.semantics == ArgumentationSemantics.PREFERRED
    assert profile.admissibility.pessimism_index == 0.25
    # Unspecified sections fall back to their defaults.
    assert profile.revision == RevisionPolicy()
