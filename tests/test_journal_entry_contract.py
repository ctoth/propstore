"""WS-J Step 4a: transition journals store replay-dispatch contracts."""

from __future__ import annotations

from propstore.canonical_json import canonical_dumps
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.history import TransitionJournalEntry, TransitionOperation
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_ws_j_transition_journal_entry_has_typed_replay_contract() -> None:
    """Codex 2.12: a journal entry must carry enough typed data to replay."""

    from propstore.support_revision.history import JournalOperator

    base, entrenchment, _, ids = _history_sensitive_base()
    state_in = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("journal_contract_new")
    result, state_out = iterated_revise(
        state_in,
        new_atom,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
        operator="restrained",
    )
    operation = TransitionOperation(
        name="iterated_revise",
        input_atom_id=new_atom.atom_id,
        target_atom_ids=(ids["legacy"],),
    )
    version_policy_snapshot = {
        "revision_policy_version": "revision.v1",
        "ranking_policy_version": "ranking.v1",
        "entrenchment_policy_version": "entrenchment.v1",
    }
    operator_input = {
        "formula": belief_atom_to_canonical_dict(new_atom),
        "revision_operator": "restrained",
        "targets": [ids["legacy"]],
    }

    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id="policy:revision/default",
        operator=JournalOperator.ITERATED_REVISE,
        operator_input=operator_input,
        version_policy_snapshot=version_policy_snapshot,
        state_out=state_out,
        explanation=result.explanation,
    )

    payload = entry.to_dict()

    assert entry.operator is JournalOperator.ITERATED_REVISE
    assert payload["operator"] == "iterated_revise"
    assert payload["operator_input"] == operator_input
    assert payload["version_policy_snapshot"] == version_policy_snapshot
    assert payload["normalized_state_in"] == state_in.to_canonical_dict()
    assert payload["normalized_state_out"] == state_out.to_canonical_dict()
    canonical_dumps(payload["operator_input"])
    canonical_dumps(payload["version_policy_snapshot"])
    canonical_dumps(payload["normalized_state_in"])
    canonical_dumps(payload["normalized_state_out"])

    replayed = dispatch(
        entry.operator,
        state_in=entry.normalized_state_in,
        operator_input=entry.operator_input,
        policy=entry.version_policy_snapshot,
    )
    assert replayed.to_canonical_dict() == entry.normalized_state_out
