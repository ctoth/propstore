"""Epistemic snapshot and journal tests."""

from __future__ import annotations

import pytest

from quire.documents.schema import DocumentSchemaError

from propstore.support_revision.operator_inputs import (
    IteratedReviseInput,
)
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
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


def test_epistemic_snapshot_rejects_removed_entrenchment_override_field() -> None:
    from propstore.support_revision.history import EpistemicSnapshot

    base, entrenchment, _, _ = _history_sensitive_base()
    payload = EpistemicSnapshot.from_state(
        make_epistemic_state(base, entrenchment)
    ).to_dict()
    reasons = payload["state"]["entrenchment_reasons"]
    reason = next(iter(reasons.values()))
    reason["override_priority"] = 0

    with pytest.raises(DocumentSchemaError, match="override_priority"):
        EpistemicSnapshot.from_mapping(payload)


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
    )

    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id="policy:revision/default",
        operator=JournalOperator.ITERATED_REVISE,
        operator_input=IteratedReviseInput(
            formula=new_atom, revision_operator="restrained", max_candidates=8
        ),
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

    assert payload["content_hash"] == entry.content_hash
    assert payload["state_in"]["content_hash"] == entry.state_in.content_hash
    assert payload["state_out"]["content_hash"] == entry.state_out.content_hash
    assert payload["policy_id"] == "policy:revision/default"
    assert payload["operator"] == "iterated_revise"
    assert payload["operator_input"]["revision_operator"] == "restrained"
    assert payload["version_policy_snapshot"]["ranking_policy_version"] == "ranking.v1"
    assert replay.ok is True
    assert replay.checked_entry_hashes == (entry.content_hash,)


def test_journal_entry_fingerprint_ignores_unset_optional_fields() -> None:
    """An unset optional field must not reach the fingerprint.

    A field left at ``None`` and a field simply absent are the same fact, and
    encoders disagree about which they emit: the charter's JSON drops an unset
    optional that the in-memory lowering keeps. If nulls reached the hash, the
    same entry would fingerprint two ways depending on which encoder produced
    the payload — which is how a stored journal came to fail its own hash check.
    """
    from propstore.support_revision.history import _stable_hash

    with_null = {
        "a": 1,
        "b": None,
        "nested": {"x": None, "y": 2},
        "items": [{"z": None}],
    }
    without_null = {"a": 1, "nested": {"y": 2}, "items": [{}]}

    assert _stable_hash(with_null) == _stable_hash(without_null)


def test_journal_entry_fingerprint_still_separates_real_content() -> None:
    from propstore.support_revision.history import _stable_hash

    assert _stable_hash({"a": 1}) != _stable_hash({"a": 2})
