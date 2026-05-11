from __future__ import annotations

from dataclasses import replace

import pytest

from belief_set import Atom, TOP, disjunction

from propstore.support_revision.belief_set_adapter import decide_ic_merge, decide_ic_merge_profile
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator, TransitionJournal, TransitionOperation
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.realization import realize_ic_merge_decision
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionMergeRequiredFailure, RevisionScope
from propstore.worldline.definition import WorldlineRevisionQuery
from tests.fixtures.journal import make_journal_entry
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


def test_ic_merge_decision_report_records_profile_multiset_and_integrity_constraint() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "atom", "atom_id": "atom:a"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    trace = decision.report.trace
    assert trace["profile_atom_ids"] == [["atom:a"], ["atom:a"], ["atom:b"]]
    assert trace["integrity_constraint"] == {"kind": "atom", "atom_id": "atom:a"}


def test_ic_merge_decision_report_records_selected_worlds_hash() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "atom", "atom_id": "atom:a"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    trace = decision.report.trace
    assert isinstance(trace["selected_worlds_hash"], str)
    assert len(trace["selected_worlds_hash"]) == 64
    assert isinstance(trace["scored_worlds_hash"], str)
    assert len(trace["scored_worlds_hash"]) == 64


def test_ic_merge_decision_report_records_formal_operator_family() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="gmax",
        max_alphabet_size=4,
    )

    assert decision.report.operation == "ic_merge"
    assert decision.report.policy == "belief_set.ic_merge.merge_belief_profile.gmax"
    assert decision.report.trace["merge_operator"] == "gmax"


def test_ic_merge_decision_preserves_duplicate_profile_members() -> None:
    duplicate_decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )
    unique_decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    assert duplicate_decision.report.trace["profile_atom_ids"] == [["atom:a"], ["atom:a"], ["atom:b"]]
    assert duplicate_decision.report.trace["profile_hash"] != unique_decision.report.trace["profile_hash"]


def test_realizable_ic_merge_returns_epistemic_state_instead_of_realization_not_implemented() -> None:
    state, atom_ids = _merge_state()

    next_state = _dispatch_realizable_merge(state, atom_ids)

    assert next_state.history[-1].operator == "ic_merge"
    assert next_state.history[-1].event is not None
    assert next_state.history[-1].event.realization_failure is None


def test_realized_ic_merge_accepts_exact_atoms_from_selected_world() -> None:
    state, atom_ids = _merge_state()

    next_state = _dispatch_realizable_merge(state, atom_ids)

    assert atom_ids["a"] in next_state.accepted_atom_ids


def test_realized_ic_merge_rejects_atoms_false_in_selected_world() -> None:
    state, atom_ids = _merge_state()

    next_state = _dispatch_realizable_merge(state, atom_ids)

    assert atom_ids["b"] in next_state.history[-1].rejected_atom_ids
    assert atom_ids["b"] not in next_state.accepted_atom_ids


def test_realized_ic_merge_preserves_support_for_surviving_atoms() -> None:
    state, atom_ids = _merge_state()

    next_state = _dispatch_realizable_merge(state, atom_ids)

    assert next_state.base.support_sets[atom_ids["a"]] == (("assumption:support_a",),)


def test_realized_ic_merge_records_realization_report_in_event() -> None:
    state, atom_ids = _merge_state()

    next_state = _dispatch_realizable_merge(state, atom_ids)

    event = next_state.history[-1].event
    assert event is not None
    assert event.decision is not None
    assert event.realization is not None
    assert event.realization.accepted_atom_ids == (atom_ids["a"],)
    assert event.realization.rejected_atom_ids == (atom_ids["b"],)
    assert event.realization.reasons[atom_ids["a"]].selection_rule == "ic_merge_selected_world"
    assert event.realization.reasons[atom_ids["b"]].reason == "ic_merge_world_false"


def test_disjunctive_selected_worlds_fail_with_typed_ambiguous_realization() -> None:
    state, atom_ids = _merge_state()
    decision = decide_ic_merge(
        frozenset((atom_ids["a"], atom_ids["b"])),
        (TOP,),
        disjunction(Atom(atom_ids["a"]), Atom(atom_ids["b"])),
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        realize_ic_merge_decision(state.base, decision)

    assert exc_info.value.reason == "ambiguous_selected_worlds"
    assert exc_info.value.decision_report is not None
    assert exc_info.value.selected_worlds_hash == decision.report.trace["selected_worlds_hash"]


def test_selected_world_with_unknown_formal_atom_fails_typed() -> None:
    state, atom_ids = _merge_state()
    unknown_atom_id = "ps:assertion:unknown-formal-atom"

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        _dispatch_merge(
            state,
            profile_atom_ids=[[unknown_atom_id], [atom_ids["a"]]],
            integrity_constraint={
                "kind": "literals",
                "required": [unknown_atom_id],
                "forbidden": [atom_ids["a"]],
            },
        )

    assert exc_info.value.reason == "unmapped_formal_atom"
    assert exc_info.value.decision_report is not None
    assert exc_info.value.selected_worlds_hash == exc_info.value.decision_report.trace["selected_worlds_hash"]


def test_unsatisfiable_integrity_constraint_preserves_formal_decision() -> None:
    state, atom_ids = _merge_state()

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        _dispatch_merge(
            state,
            profile_atom_ids=[[atom_ids["a"]]],
            integrity_constraint={
                "kind": "literals",
                "required": [atom_ids["a"]],
                "forbidden": [atom_ids["a"]],
            },
        )

    assert exc_info.value.reason == "unsatisfiable_integrity_constraint"
    assert exc_info.value.decision_report is not None
    assert exc_info.value.integrity_constraint == {
        "kind": "literals",
        "required": [atom_ids["a"]],
        "forbidden": [atom_ids["a"]],
    }


def test_unrealizable_merge_failure_event_preserves_selected_world_hash() -> None:
    state, atom_ids = _merge_state()

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        _dispatch_unsatisfiable_merge(state, atom_ids)

    event = exc_info.value.event
    assert event is not None
    assert event.decision is not None
    assert event.realization is None
    assert event.realization_failure == "unsatisfiable_integrity_constraint"
    assert event.decision.trace["selected_worlds_hash"] == exc_info.value.selected_worlds_hash


def test_unrealizable_merge_failure_is_replayable_as_failure() -> None:
    state, atom_ids = _merge_state()

    with pytest.raises(RevisionMergeRequiredFailure) as first:
        _dispatch_unsatisfiable_merge(state, atom_ids)
    with pytest.raises(RevisionMergeRequiredFailure) as second:
        _dispatch_unsatisfiable_merge(state, atom_ids)

    assert first.value.reason == second.value.reason == "unsatisfiable_integrity_constraint"
    assert first.value.event is not None
    assert second.value.event is not None
    assert first.value.event.content_hash == second.value.event.content_hash


def test_ic_merge_journal_replay_reconstructs_realized_state() -> None:
    journal = _realizable_ic_merge_journal()

    replayed = journal.replay()

    assert replayed.ok
    assert not replayed.errors
    assert not replayed.divergences


def test_ic_merge_replay_rejects_profile_drift() -> None:
    journal = _realizable_ic_merge_journal()
    entry = journal.entries[0]
    drifted_input = dict(entry.operator_input)
    drifted_input["profile_atom_ids"] = [[entry.operation.target_atom_ids[0]]]
    drifted = TransitionJournal(entries=(replace(entry, operator_input=drifted_input),))

    replayed = drifted.replay()

    assert not replayed.ok
    assert replayed.errors or replayed.divergences


def test_ic_merge_replay_rejects_integrity_constraint_drift() -> None:
    journal = _realizable_ic_merge_journal()
    entry = journal.entries[0]
    drifted_input = dict(entry.operator_input)
    drifted_input["integrity_constraint"] = {
        "kind": "literals",
        "required": [entry.operation.target_atom_ids[1]],
        "forbidden": [entry.operation.target_atom_ids[0]],
    }
    drifted = TransitionJournal(entries=(replace(entry, operator_input=drifted_input),))

    replayed = drifted.replay()

    assert not replayed.ok
    assert replayed.errors or replayed.divergences


def test_ic_merge_replay_rejects_policy_drift_before_semantic_replay() -> None:
    journal = _realizable_ic_merge_journal()
    entry = journal.entries[0]
    drifted = TransitionJournal(
        entries=(
            replace(
                entry,
                version_policy_snapshot={
                    **entry.version_policy_snapshot,
                    "revision_policy_version": "revision.v2",
                },
            ),
        )
    )

    replayed = drifted.replay()

    assert not replayed.ok
    assert replayed.errors
    assert "policy snapshot mismatch" in replayed.errors[0]


def test_worldline_capture_serializes_ic_merge_event() -> None:
    state, atom_ids = _merge_state()
    query = WorldlineRevisionQuery.from_dict({
        "operation": "ic_merge",
        "profile_atom_ids": [[atom_ids["a"]], [atom_ids["b"]]],
        "integrity_constraint": {
            "kind": "literals",
            "required": [atom_ids["a"]],
            "forbidden": [atom_ids["b"]],
        },
        "merge_parent_commits": ["left", "right"],
        "merge_operator": "sigma",
        "max_alphabet_size": 8,
    })
    assert query is not None

    journal = _capture_journal_for(state, (query,))

    payload = journal.to_dict()
    entry = payload["entries"][0]
    assert entry["operator"] == "ic_merge"
    assert entry["operator_input"]["merge_parent_commits"] == ["left", "right"]
    assert entry["operator_input"]["integrity_constraint"]["required"] == [atom_ids["a"]]
    event = entry["normalized_state_out"]["history"][-1]["event"]
    assert event["operation"] == "ic_merge"
    assert event["decision"]["trace"]["merge_operator"] == "sigma"
    assert event["realization"]["rejected_atom_ids"] == [atom_ids["b"]]


def _dispatch_realizable_merge(state, atom_ids: dict[str, str]):
    return _dispatch_merge(
        state,
        profile_atom_ids=[[atom_ids["a"]], [atom_ids["b"]]],
        integrity_constraint={
            "kind": "literals",
            "required": [atom_ids["a"]],
            "forbidden": [atom_ids["b"]],
        },
    )


def _dispatch_merge(state, *, profile_atom_ids, integrity_constraint):
    return dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input={
            "profile_atom_ids": profile_atom_ids,
            "integrity_constraint": integrity_constraint,
            "merge_operator": "sigma",
            "max_candidates": 8,
        },
        policy=_POLICY,
    )


def _dispatch_unsatisfiable_merge(state, atom_ids: dict[str, str]):
    return _dispatch_merge(
        state,
        profile_atom_ids=[[atom_ids["a"]]],
        integrity_constraint={
            "kind": "literals",
            "required": [atom_ids["a"]],
            "forbidden": [atom_ids["a"]],
        },
    )


def _realizable_ic_merge_journal() -> TransitionJournal:
    state, atom_ids = _merge_state()
    operator_input = {
        "profile_atom_ids": [[atom_ids["a"]], [atom_ids["b"]]],
        "merge_parent_commits": ["left", "right"],
        "integrity_constraint": {
            "kind": "literals",
            "required": [atom_ids["a"]],
            "forbidden": [atom_ids["b"]],
        },
        "merge_operator": "sigma",
        "max_alphabet_size": 8,
    }
    state_out = dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input=operator_input,
        policy=_POLICY,
    )
    return TransitionJournal(
        entries=(
            make_journal_entry(
                state_in=state,
                operation=TransitionOperation(
                    name="ic_merge",
                    target_atom_ids=(atom_ids["a"], atom_ids["b"]),
                    parameters=operator_input,
                ),
                operator=JournalOperator.IC_MERGE,
                operator_input=operator_input,
                state_out=state_out,
                policy=_POLICY,
            ),
        )
    )


def _capture_journal_for(state, queries):
    from propstore.worldline.revision_capture import capture_journal

    class _Bound:
        def epistemic_state(self):
            return state

    return capture_journal(_Bound(), queries, policy_id="policy:revision/default")


def _merge_state():
    atom_a = make_assertion_atom("ic_merge_a")
    atom_b = make_assertion_atom("ic_merge_b")
    base = BeliefBase(
        scope=RevisionScope(
            bindings={},
            branch="topic",
            merge_parent_commits=("left", "right"),
        ),
        atoms=(
            AssumptionAtom("assumption:support_a", {"assumption_id": "support_a"}),
            AssumptionAtom("assumption:support_b", {"assumption_id": "support_b"}),
            atom_a,
            atom_b,
        ),
        support_sets={
            atom_a.atom_id: (("assumption:support_a",),),
            atom_b.atom_id: (("assumption:support_b",),),
        },
        essential_support={
            atom_a.atom_id: ("assumption:support_a",),
            atom_b.atom_id: ("assumption:support_b",),
        },
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(atom.atom_id for atom in base.atoms),
        reasons={},
    )
    state = make_epistemic_state(base, entrenchment=entrenchment)
    return state, {"a": atom_a.atom_id, "b": atom_b.atom_id}
