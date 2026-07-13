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


def test_identical_policy_collapses_to_one_identity() -> None:
    # The point of the profile: identity is derived from content, so two runs
    # under the same policy are the same policy. (There is no from_dict to test
    # a round trip through — nothing parses a profile back from a payload; the
    # journal only ever writes one.)
    def _profile() -> PolicyProfile:
        return PolicyProfile(
            revision=RevisionPolicy(operator="lexicographic", allow_reintroduction=True),
            merge=MergePolicy(operator=MergeOperator.MAX, branch_filter=("main", "rc")),
            admissibility=AdmissibilityProfile(
                semantics=ArgumentationSemantics.PREFERRED,
                reasoning_backend=ReasoningBackend.ATMS,
            ),
            label="experiment",
        )

    assert _profile().profile_id == _profile().profile_id
    assert _profile().content_hash == _profile().content_hash
    assert _profile().merge.branch_filter == ("main", "rc")


def test_differing_policy_gets_a_different_identity() -> None:
    default = default_policy_profile()
    other = PolicyProfile(revision=RevisionPolicy(operator="lexicographic"))

    assert other.profile_id != default.profile_id
    assert other.content_hash != default.content_hash


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
