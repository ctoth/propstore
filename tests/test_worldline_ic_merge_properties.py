from __future__ import annotations

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from belief_set import Atom, TOP, disjunction

from propstore.support_revision.belief_set_adapter import decide_ic_merge, decide_ic_merge_profile
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator, TransitionJournal, TransitionOperation
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.realization import realize_ic_merge_decision
from propstore.support_revision.state import BeliefBase, RevisionMergeRequiredFailure, RevisionScope
from tests.fixtures.journal import make_journal_entry
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


@settings(max_examples=50)
@given(count=st.integers(min_value=1, max_value=5), ic_index=st.integers(min_value=0, max_value=4))
@example(count=2, ic_index=1)
def test_ic0_ic_atom_not_present_in_profile_is_still_realized(count: int, ic_index: int) -> None:
    state, atom_ids = _state_with_atoms(count)
    ic_atom_id = atom_ids[ic_index % count]

    next_state = _dispatch_merge(
        state,
        profile_atom_ids=[[]],
        integrity_constraint={"kind": "atom", "atom_id": ic_atom_id},
        merge_operator="sigma",
    )

    assert ic_atom_id in next_state.accepted_atom_ids


@settings(max_examples=50)
@given(count=st.integers(min_value=1, max_value=5), merge_operator=st.sampled_from(("sigma", "gmax")))
@example(count=2, merge_operator="sigma")
def test_ic2_consistent_profile_and_ic_realizes_their_conjunction(count: int, merge_operator: str) -> None:
    state, atom_ids = _state_with_atoms(count)

    next_state = _dispatch_merge(
        state,
        profile_atom_ids=[list(atom_ids)],
        integrity_constraint={"kind": "top"},
        merge_operator=merge_operator,
    )

    assert set(next_state.accepted_atom_ids) == set(atom_ids)


@settings(max_examples=50)
@given(
    count=st.integers(min_value=1, max_value=5),
    profile_indexes=st.lists(
        st.lists(st.integers(min_value=0, max_value=4), min_size=0, max_size=5),
        min_size=1,
        max_size=4,
    ),
    ic_index=st.integers(min_value=0, max_value=4),
    merge_operator=st.sampled_from(("sigma", "gmax")),
)
def test_ic0_realized_success_satisfies_integrity_constraint(
    count: int,
    profile_indexes: list[list[int]],
    ic_index: int,
    merge_operator: str,
) -> None:
    state, atom_ids = _state_with_atoms(count)
    ic_atom_id = atom_ids[ic_index % count]

    try:
        next_state = _dispatch_merge(
            state,
            profile_atom_ids=_profile_from_indexes(profile_indexes, atom_ids),
            integrity_constraint={"kind": "atom", "atom_id": ic_atom_id},
            merge_operator=merge_operator,
        )
    except RevisionMergeRequiredFailure:
        return

    assert ic_atom_id in next_state.accepted_atom_ids


@settings(max_examples=50)
@given(count=st.integers(min_value=1, max_value=5), merge_operator=st.sampled_from(("sigma", "gmax")))
def test_successful_realization_partitions_projected_merge_alphabet(count: int, merge_operator: str) -> None:
    state, atom_ids = _state_with_atoms(count)

    next_state = _dispatch_merge(
        state,
        profile_atom_ids=[list(atom_ids)],
        integrity_constraint={"kind": "top"},
        merge_operator=merge_operator,
    )

    event = next_state.history[-1].event
    assert event is not None
    assert event.realization is not None
    accepted = set(event.realization.accepted_atom_ids)
    rejected = set(event.realization.rejected_atom_ids)
    projected = set(event.decision.input_formula_ids if event.decision is not None else ())
    assert accepted.isdisjoint(rejected)
    assert accepted | rejected == projected


@settings(max_examples=25)
@given(count=st.integers(min_value=1, max_value=5))
def test_profile_multiset_hash_preserves_duplicate_entries(count: int) -> None:
    _, atom_ids = _state_with_atoms(count)
    atom_id = atom_ids[0]

    duplicate = decide_ic_merge_profile(
        profile_atom_ids=((atom_id,), (atom_id,)),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=8,
    )
    unique = decide_ic_merge_profile(
        profile_atom_ids=((atom_id,),),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=8,
    )

    assert duplicate.report.trace["profile_hash"] != unique.report.trace["profile_hash"]


@settings(max_examples=25)
@given(count=st.integers(min_value=1, max_value=5))
def test_ic_merge_journal_replay_matches_direct_dispatch(count: int) -> None:
    state, atom_ids = _state_with_atoms(count)
    operator_input = {
        "profile_atom_ids": [list(atom_ids)],
        "integrity_constraint": {"kind": "top"},
        "merge_operator": "sigma",
        "max_candidates": 32,
    }
    direct = dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input=operator_input,
        policy=_POLICY,
    )
    journal = TransitionJournal(
        entries=(
            make_journal_entry(
                state_in=state,
                operation=TransitionOperation(
                    name="ic_merge",
                    target_atom_ids=tuple(atom_ids),
                    parameters=operator_input,
                ),
                operator=JournalOperator.IC_MERGE,
                operator_input=operator_input,
                state_out=direct,
                policy=_POLICY,
            ),
        )
    )

    replayed = journal.replay()

    assert replayed.ok
    assert not replayed.errors
    assert not replayed.divergences


@settings(max_examples=25)
@given(count=st.integers(min_value=2, max_value=5))
def test_event_hash_changes_when_ic_or_policy_changes(count: int) -> None:
    state, atom_ids = _state_with_atoms(count)

    first = _dispatch_merge(
        state,
        profile_atom_ids=[list(atom_ids)],
        integrity_constraint={"kind": "atom", "atom_id": atom_ids[0]},
        merge_operator="sigma",
    )
    second = _dispatch_merge(
        state,
        profile_atom_ids=[list(atom_ids)],
        integrity_constraint={"kind": "atom", "atom_id": atom_ids[1]},
        merge_operator="sigma",
    )
    third = dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input={
            "profile_atom_ids": [list(atom_ids)],
            "integrity_constraint": {"kind": "atom", "atom_id": atom_ids[0]},
            "merge_operator": "sigma",
            "max_candidates": 32,
        },
        policy={**_POLICY, "revision_policy_version": "revision.v2"},
    )

    assert first.history[-1].event is not None
    assert second.history[-1].event is not None
    assert third.history[-1].event is not None
    assert first.history[-1].event.content_hash != second.history[-1].event.content_hash
    assert first.history[-1].event.content_hash != third.history[-1].event.content_hash


@settings(max_examples=25)
@given(count=st.integers(min_value=1, max_value=5))
def test_mapping_totality_succeeds_iff_selected_atoms_are_known(count: int) -> None:
    state, atom_ids = _state_with_atoms(count)
    unknown_atom_id = "ps:assertion:hypothesis-unknown"

    next_state = _dispatch_merge(
        state,
        profile_atom_ids=[[atom_ids[0]]],
        integrity_constraint={"kind": "atom", "atom_id": atom_ids[0]},
        merge_operator="sigma",
    )
    assert atom_ids[0] in next_state.accepted_atom_ids

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        _dispatch_merge(
            state,
            profile_atom_ids=[[unknown_atom_id]],
            integrity_constraint={"kind": "atom", "atom_id": unknown_atom_id},
            merge_operator="sigma",
        )

    assert exc_info.value.reason == "unmapped_formal_atom"


@example(count=2)
@settings(max_examples=10)
@given(count=st.integers(min_value=2, max_value=5))
def test_ambiguous_two_world_result_fails_typed(count: int) -> None:
    state, atom_ids = _state_with_atoms(count)
    decision = decide_ic_merge(
        frozenset((atom_ids[0], atom_ids[1])),
        (TOP,),
        disjunction(Atom(atom_ids[0]), Atom(atom_ids[1])),
        merge_operator="sigma",
        max_alphabet_size=8,
    )

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        realize_ic_merge_decision(state.base, decision)

    assert exc_info.value.reason == "ambiguous_selected_worlds"


def test_generated_ic_merge_path_does_not_call_assignment_selection_merge(monkeypatch) -> None:
    from propstore.world import assignment_selection_merge

    def _fail(*args, **kwargs):
        raise AssertionError("IC merge realization must not call assignment-selection merge")

    monkeypatch.setattr(assignment_selection_merge, "solve_assignment_selection_merge", _fail)
    state, atom_ids = _state_with_atoms(2)

    next_state = _dispatch_merge(
        state,
        profile_atom_ids=[list(atom_ids)],
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
    )

    assert set(next_state.accepted_atom_ids) == set(atom_ids)


def _dispatch_merge(
    state,
    *,
    profile_atom_ids: list[list[str]],
    integrity_constraint: dict[str, object],
    merge_operator: str,
):
    return dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input={
            "profile_atom_ids": profile_atom_ids,
            "integrity_constraint": integrity_constraint,
            "merge_operator": merge_operator,
            "max_candidates": 32,
        },
        policy=_POLICY,
    )


def _state_with_atoms(count: int):
    atoms = tuple(make_assertion_atom(f"ic_merge_property_{index}") for index in range(count))
    base = BeliefBase(
        scope=RevisionScope(bindings={}, branch="topic", merge_parent_commits=("left", "right")),
        atoms=atoms,
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(atom.atom_id for atom in atoms),
        reasons={},
    )
    state = make_epistemic_state(base, entrenchment=entrenchment)
    return state, tuple(atom.atom_id for atom in atoms)


def _profile_from_indexes(index_profiles: list[list[int]], atom_ids: tuple[str, ...]) -> list[list[str]]:
    return [
        [atom_ids[index % len(atom_ids)] for index in profile]
        for profile in index_profiles
    ]
