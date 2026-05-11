from __future__ import annotations

import pytest

from propstore.support_revision.belief_set_adapter import decide_ic_merge_profile
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionMergeRequiredFailure, RevisionScope
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

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        _dispatch_merge(
            state,
            profile_atom_ids=[[atom_ids["a"]], [atom_ids["b"]]],
            integrity_constraint={"kind": "top"},
        )

    assert exc_info.value.reason == "ambiguous_selected_worlds"
    assert exc_info.value.decision_report is not None
    assert exc_info.value.profile_atom_ids == ((atom_ids["a"],), (atom_ids["b"],))


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
        _dispatch_merge(
            state,
            profile_atom_ids=[[atom_ids["a"]], [atom_ids["b"]]],
            integrity_constraint={"kind": "top"},
        )

    event = exc_info.value.event
    assert event is not None
    assert event.decision is not None
    assert event.realization is None
    assert event.realization_failure == "ambiguous_selected_worlds"
    assert event.decision.trace["selected_worlds_hash"] == exc_info.value.selected_worlds_hash


def test_unrealizable_merge_failure_is_replayable_as_failure() -> None:
    state, atom_ids = _merge_state()
    kwargs = {
        "profile_atom_ids": [[atom_ids["a"]], [atom_ids["b"]]],
        "integrity_constraint": {"kind": "top"},
    }

    with pytest.raises(RevisionMergeRequiredFailure) as first:
        _dispatch_merge(state, **kwargs)
    with pytest.raises(RevisionMergeRequiredFailure) as second:
        _dispatch_merge(state, **kwargs)

    assert first.value.reason == second.value.reason == "ambiguous_selected_worlds"
    assert first.value.event is not None
    assert second.value.event is not None
    assert first.value.event.content_hash == second.value.event.content_hash


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
