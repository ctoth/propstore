from __future__ import annotations

from dataclasses import replace

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


def _state_for_atoms(atoms, *, accepted_atom_ids: tuple[str, ...]) -> EpistemicState:
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=tuple(atoms))
    return EpistemicState(
        scope=base.scope,
        base=base,
        accepted_atom_ids=accepted_atom_ids,
        ranked_atom_ids=tuple(atom.atom_id for atom in atoms),
        ranking={atom.atom_id: index for index, atom in enumerate(atoms)},
    )
