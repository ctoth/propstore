from __future__ import annotations

import pytest
from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.policies import (
    AdmissibilityProfile,
    MergePolicy,
    PolicyProfile,
    RevisionPolicy,
    SourceTrustProfile,
    default_policy_profile,
    policy_assertions,
)
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_policy_profile_roundtrips_with_stable_content_identity() -> None:
    profile = default_policy_profile()

    restored = PolicyProfile.from_dict(profile.to_dict())

    assert restored == profile
    assert restored.profile_id == profile.profile_id
    assert restored.content_hash == profile.content_hash
    assert profile.profile_id.startswith("urn:propstore:policy-profile:")


def test_policy_profile_identity_changes_when_governance_policy_changes() -> None:
    profile = default_policy_profile()
    changed = replace(
        profile,
        source_trust=SourceTrustProfile(
            accepted_authorities=("urn:propstore:authority:human-editor",),
            unsigned_graph_policy="reject",
        ),
    )

    assert changed.profile_id != profile.profile_id
    assert changed.content_hash != profile.content_hash


def test_transition_journal_hash_includes_full_policy_payload() -> None:
    from propstore.support_revision.history import (
        JournalOperator,
        TransitionJournalEntry,
        TransitionOperation,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    state_in = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("policy_journal_new")
    result, state_out = iterated_revise(
        state_in,
        new_atom,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
        operator="restrained",
    )
    operation = TransitionOperation(
        name="iterated_revise",
        input_atom_id=new_atom.atom_id,
        target_atom_ids=(ids["legacy"],),
    )
    profile = default_policy_profile()
    changed = replace(
        profile,
        revision=RevisionPolicy(operator="natural"),
    )

    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id=profile.profile_id,
        policy_payload=profile.to_dict(),
        operator=JournalOperator.ITERATED_REVISE,
        operator_input={
            "formula": belief_atom_to_canonical_dict(new_atom),
            "max_candidates": 8,
            "revision_operator": "restrained",
            "targets": [ids["legacy"]],
        },
        version_policy_snapshot={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v1",
            "entrenchment_policy_version": "entrenchment.v1",
        },
        state_out=state_out,
        explanation=result.explanation,
    )
    changed_entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id=profile.profile_id,
        policy_payload=changed.to_dict(),
        operator=JournalOperator.ITERATED_REVISE,
        operator_input={
            "formula": belief_atom_to_canonical_dict(new_atom),
            "max_candidates": 8,
            "revision_operator": "restrained",
            "targets": [ids["legacy"]],
        },
        version_policy_snapshot={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v1",
            "entrenchment_policy_version": "entrenchment.v1",
        },
        state_out=state_out,
        explanation=result.explanation,
    )

    assert entry.to_dict()["policy"]["profile_id"] == profile.profile_id
    assert entry.content_hash != changed_entry.content_hash


def test_policy_profile_projects_to_situated_assertions() -> None:
    profile = default_policy_profile()

    assertions = policy_assertions(profile, context_id="ps:context:governance")

    relation_ids = {str(assertion.relation.concept_id) for assertion in assertions}
    assert "ps:concept:policy-profile" in relation_ids
    assert "ps:concept:policy-revision" in relation_ids
    assert "ps:concept:policy-merge" in relation_ids
    assert all(str(assertion.context.id) == "ps:context:governance" for assertion in assertions)


def test_worldline_content_hash_changes_when_policy_profile_changes() -> None:
    from propstore.worldline import compute_worldline_content_hash
    from propstore.worldline.result_types import WorldlineDependencies, WorldlineTargetValue

    profile = default_policy_profile()
    changed = replace(
        profile,
        admissibility=AdmissibilityProfile(comparison="democratic", link="weakest"),
    )

    left = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=None,
        policy=profile.to_dict(),
    )
    right = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=None,
        policy=changed.to_dict(),
    )

    assert left != right


_token = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True)


@settings(deadline=None)
@pytest.mark.property
@given(
    operator=_token,
    merge_operator=st.sampled_from(["sigma", "max", "gmax"]),
    comparison=st.sampled_from(["elitist", "democratic"]),
    link=st.sampled_from(["last", "weakest"]),
)
def test_policy_serialization_roundtrip_property(
    operator: str,
    merge_operator: str,
    comparison: str,
    link: str,
) -> None:
    profile = PolicyProfile(
        revision=RevisionPolicy(operator=operator),
        merge=MergePolicy(operator=merge_operator),
        admissibility=AdmissibilityProfile(comparison=comparison, link=link),
    )

    restored = PolicyProfile.from_dict(profile.to_dict())

    assert restored == profile
    assert restored.profile_id == profile.profile_id
