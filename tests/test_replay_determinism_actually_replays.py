"""WS-J Step 4b: journal replay re-executes recorded operators."""

from __future__ import annotations

from propstore.support_revision.history import (
    EpistemicSnapshot,
    JournalOperator,
    TransitionJournal,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_ws_j_journal_replay_reports_algorithmic_divergence() -> None:
    """Hash-chain integrity is weaker than replaying the recorded operator."""

    base, entrenchment, _, ids = _history_sensitive_base()
    state_in = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("journal_replay_new")
    operation = TransitionOperation(
        name="iterated_revise",
        input_atom_id=new_atom.atom_id,
        target_atom_ids=(ids["legacy"],),
    )
    operator_input = {
        "formula": belief_atom_to_canonical_dict(new_atom),
        "revision_operator": "restrained",
        "targets": [ids["legacy"]],
    }
    version_policy_snapshot = {
        "revision_policy_version": "revision.v1",
        "ranking_policy_version": "ranking.v1",
        "entrenchment_policy_version": "entrenchment.v1",
    }
    bad_entry = TransitionJournalEntry(
        state_in=EpistemicSnapshot.from_state(state_in),
        operation=operation,
        policy_id="policy:revision/default",
        operator=JournalOperator.ITERATED_REVISE,
        operator_input=operator_input,
        version_policy_snapshot=version_policy_snapshot,
        normalized_state_in=state_in.to_canonical_dict(),
        normalized_state_out=state_in.to_canonical_dict(),
        state_out=EpistemicSnapshot.from_state(state_in),
    )
    journal = TransitionJournal(entries=(bad_entry,))

    assert journal.check_chain_integrity().ok is True
    replay = journal.replay()

    assert replay.ok is False
    assert replay.divergences[0].entry_index == 0
    assert replay.divergences[0].operator is JournalOperator.ITERATED_REVISE
    assert replay.divergences[0].operator_input == operator_input
