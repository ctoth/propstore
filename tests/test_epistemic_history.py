"""Epistemic snapshot, journal, and semantic diff tests."""

from __future__ import annotations

import pytest
from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.core.active_claims import ActiveClaim
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from propstore.support_revision.state import BeliefBase, EpistemicState
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_epistemic_snapshot_roundtrips_with_stable_hash() -> None:
    from propstore.support_revision.history import EpistemicSnapshot

    base, entrenchment, _, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)

    snapshot = EpistemicSnapshot.from_state(state)
    payload = snapshot.to_dict()
    restored = EpistemicSnapshot.from_mapping(payload)

    assert payload["content_hash"] == snapshot.content_hash
    assert restored == snapshot
    assert restored.to_canonical_json() == snapshot.to_canonical_json()
    assert restored.content_hash == snapshot.content_hash


def test_transition_journal_records_state_policy_operator_and_replay_hashes() -> None:
    from propstore.support_revision.history import (
        JournalOperator,
        TransitionJournal,
        TransitionJournalEntry,
        TransitionOperation,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    state_in = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("journal_new")
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
        parameters={"conflicts": {new_atom.atom_id: [ids["legacy"]]}},
    )

    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id="policy:revision/default",
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
    journal = TransitionJournal(entries=(entry,))
    payload = entry.to_dict()
    replay = journal.check_chain_integrity()

    assert payload["state_in_hash"] == entry.state_in.content_hash
    assert payload["state_out_hash"] == entry.state_out.content_hash
    assert payload["policy_id"] == "policy:revision/default"
    assert payload["operator"] == "iterated_revise"
    assert payload["operator_input"]["revision_operator"] == "restrained"
    assert payload["version_policy_snapshot"]["ranking_policy_version"] == "ranking.v1"
    assert replay.ok is True
    assert replay.checked_entry_hashes == (entry.content_hash,)


def test_semantic_diff_applies_assertion_warrant_ranking_provenance_and_dependency_deltas() -> None:
    from propstore.support_revision.history import (
        apply_epistemic_diff,
        diff_epistemic_snapshots,
        EpistemicSnapshot,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    source_state = make_epistemic_state(base, entrenchment)
    target_state = _changed_semantic_state(source_state, ids["legacy"])

    source = EpistemicSnapshot.from_state(source_state)
    target = EpistemicSnapshot.from_state(target_state)
    diff = diff_epistemic_snapshots(source, target)

    assert {
        "assertion_acceptance",
        "warrant",
        "ranking",
        "provenance",
        "dependency",
    }.issubset({delta.surface for delta in diff.deltas})
    assert apply_epistemic_diff(source, diff) == target


@pytest.mark.property
@given(source_accepts=st.booleans(), target_accepts=st.booleans())
@settings(max_examples=12)
def test_semantic_diff_apply_roundtrips_generated_tiny_assertion_languages(
    source_accepts: bool,
    target_accepts: bool,
) -> None:
    from propstore.support_revision.history import (
        apply_epistemic_diff,
        diff_epistemic_snapshots,
        EpistemicSnapshot,
    )

    atom = make_assertion_atom("generated")
    base = BeliefBase(scope=_history_sensitive_base()[0].scope, atoms=(atom,))
    entrenchment = EntrenchmentReport(ranked_atom_ids=(atom.atom_id,))
    accepted_source = (atom.atom_id,) if source_accepts else ()
    accepted_target = (atom.atom_id,) if target_accepts else ()
    source_state = replace(
        make_epistemic_state(base, entrenchment),
        accepted_atom_ids=accepted_source,
    )
    target_state = replace(source_state, accepted_atom_ids=accepted_target)
    source = EpistemicSnapshot.from_state(source_state)
    target = EpistemicSnapshot.from_state(target_state)

    assert apply_epistemic_diff(source, diff_epistemic_snapshots(source, target)) == target


def _changed_semantic_state(state: EpistemicState, legacy_id: str) -> EpistemicState:
    changed_atoms = []
    for atom in state.base.atoms:
        if atom.atom_id != legacy_id:
            changed_atoms.append(atom)
            continue
        source_claim = ActiveClaim.from_mapping(
            {
                "id": "claim_legacy_updated",
                "type": "parameter",
                "value": "legacy",
                "concept_id": "concept_legacy",
                "source_paper": "paper:updated",
            }
        )
        changed_atoms.append(replace(atom, source_claims=(source_claim,)))
    changed_base = replace(
        state.base,
        atoms=tuple(changed_atoms),
        support_sets={
            **dict(state.base.support_sets),
            legacy_id: (("assumption:left_path",),),
        },
        essential_support={
            **dict(state.base.essential_support),
            legacy_id: ("assumption:left_path",),
        },
    )
    accepted = tuple(atom_id for atom_id in state.accepted_atom_ids if atom_id != legacy_id)
    ranked = (legacy_id,) + tuple(atom_id for atom_id in state.ranked_atom_ids if atom_id != legacy_id)
    return replace(
        state,
        base=changed_base,
        accepted_atom_ids=accepted,
        ranked_atom_ids=ranked,
        ranking={atom_id: index for index, atom_id in enumerate(ranked)},
        entrenchment_reasons={
            **dict(state.entrenchment_reasons),
            legacy_id: EntrenchmentReason(support_count=1),
        },
    )
