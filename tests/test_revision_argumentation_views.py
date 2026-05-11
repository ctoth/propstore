from __future__ import annotations

from dataclasses import replace

from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.state import (
    AssumptionAtom,
    BeliefBase,
    EpistemicState,
    RevisionEpisode,
    RevisionEvent,
    RevisionScope,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def test_argumentation_view_reports_accepted_assertions_without_source_claims_as_unmapped() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    unmapped = replace(make_assertion_atom("unmapped"), source_claims=())
    state = _state_for_atoms((unmapped,), accepted_atom_ids=(unmapped.atom_id,))

    view = project_epistemic_state_argumentation_view(object(), state)

    assert view.active_claim_ids == frozenset()
    assert view.unmapped_atom_ids == (unmapped.atom_id,)


def test_argumentation_view_keeps_accepted_assumption_atoms_visible() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    assumption = AssumptionAtom("assumption:accepted", {"assumption_id": "accepted"})
    state = _state_for_atoms((assumption,), accepted_atom_ids=(assumption.atom_id,))

    view = project_epistemic_state_argumentation_view(object(), state)

    assert view.accepted_assumption_atom_ids == ("assumption:accepted",)


def test_argumentation_view_carries_revision_event_hashes() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    atom = make_assertion_atom("event_backed")
    event = RevisionEvent(
        operation="revise",
        pre_state_hash="before",
        input_atom_id=atom.atom_id,
        policy_snapshot={"revision_policy_version": "v1"},
        replay_status="replayed",
    )
    state = replace(
        _state_for_atoms((atom,), accepted_atom_ids=(atom.atom_id,)),
        history=(RevisionEpisode(operator="revise", input_atom_id=atom.atom_id, event=event),),
    )

    view = project_epistemic_state_argumentation_view(object(), state)

    assert view.revision_event_hashes == (event.content_hash,)


def test_ic_merge_argumentation_view_reports_unmapped_merge_atoms() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    accepted = replace(make_assertion_atom("ic_merge_unmapped"), source_claims=())
    rejected = make_assertion_atom("ic_merge_rejected")
    state = _realized_ic_merge_state(accepted, rejected)

    view = project_epistemic_state_argumentation_view(object(), state)

    assert view.unmapped_atom_ids == (accepted.atom_id,)


def test_ic_merge_argumentation_view_preserves_source_claim_ids() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    accepted = make_assertion_atom("ic_merge_claim_backed")
    rejected = make_assertion_atom("ic_merge_rejected_claim")
    state = _realized_ic_merge_state(accepted, rejected)

    view = project_epistemic_state_argumentation_view(object(), state)

    assert view.active_claim_ids == frozenset({"claim_ic_merge_claim_backed"})


def test_ic_merge_atms_view_preserves_support_label_minimality() -> None:
    from propstore.support_revision.af_adapter import project_epistemic_state_argumentation_view

    accepted = make_assertion_atom("ic_merge_supported")
    rejected = make_assertion_atom("ic_merge_unsupported")
    state = _realized_ic_merge_state(
        accepted,
        rejected,
        support_sets={accepted.atom_id: (("assumption:support_a",),)},
    )

    view = project_epistemic_state_argumentation_view(object(), state)

    assert state.base.support_sets[accepted.atom_id] == (("assumption:support_a",),)
    assert view.accepted_assumption_atom_ids == ("assumption:support_a",)


def test_ic_merge_rejected_atoms_explain_selected_world_false() -> None:
    accepted = make_assertion_atom("ic_merge_reason_true")
    rejected = make_assertion_atom("ic_merge_reason_false")
    state = _realized_ic_merge_state(accepted, rejected)

    event = state.history[-1].event

    assert event is not None
    assert event.realization is not None
    assert event.realization.reasons[rejected.atom_id].reason == "ic_merge_world_false"


def _state_for_atoms(atoms, *, accepted_atom_ids: tuple[str, ...]) -> EpistemicState:
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=tuple(atoms))
    return EpistemicState(
        scope=base.scope,
        base=base,
        accepted_atom_ids=accepted_atom_ids,
        ranked_atom_ids=tuple(atom.atom_id for atom in atoms),
        ranking={atom.atom_id: index for index, atom in enumerate(atoms)},
    )


def _realized_ic_merge_state(accepted, rejected, *, support_sets=None) -> EpistemicState:
    base = BeliefBase(
        scope=RevisionScope(bindings={}, branch="topic", merge_parent_commits=("left", "right")),
        atoms=(
            AssumptionAtom("assumption:support_a", {"assumption_id": "support_a"}),
            accepted,
            rejected,
        ),
        support_sets={} if support_sets is None else support_sets,
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(atom.atom_id for atom in base.atoms),
        reasons={},
    )
    state = make_epistemic_state(base, entrenchment=entrenchment)
    return dispatch(
        JournalOperator.IC_MERGE,
        state_in=state.to_canonical_dict(),
        operator_input={
            "profile_atom_ids": [[accepted.atom_id], [rejected.atom_id]],
            "integrity_constraint": {
                "kind": "literals",
                "required": [accepted.atom_id],
                "forbidden": [rejected.atom_id],
            },
            "merge_operator": "sigma",
            "max_alphabet_size": 8,
        },
        policy={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v1",
            "entrenchment_policy_version": "entrenchment.v1",
        },
    )
