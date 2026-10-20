"""Read and explicitly migrate artifacts produced before PR 321.

The frozen fixture was generated and round-tripped by the real snapshot,
journal and worldline owners at 4b865edf992f73ff7fe99f3ab7b1545e8b6bcadc.
It contains two lexical revisions, not a hand-authored approximation of v2/v5.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from msgspec.structs import replace
from quire.documents import convert_document_value, to_document_builtins

from propstore.support_revision.history import (
    EpistemicSnapshot,
    TransitionJournal,
    apply_epistemic_diff,
    diff_epistemic_snapshots,
)
from propstore.support_revision.iterated import iterated_revise
from propstore.support_revision.state import AssumptionAtom, RevisionContinuationUnavailable
from propstore.worldline.definition import WorldlineDefinition


def _fixture():
    return json.loads(
        Path("tests/fixtures/revision_state_v2_journal_v5.json").read_text(encoding="utf-8")
    )


def _journal(data) -> TransitionJournal:
    return convert_document_value(data["journal"], TransitionJournal, source="frozen v5 journal")


def test_prechange_snapshot_journal_and_worldline_remain_readable() -> None:
    data = _fixture()
    assert data["producer_commit"] == "4b865edf992f73ff7fe99f3ab7b1545e8b6bcadc"
    for name in ("initial_snapshot", "final_snapshot"):
        snapshot = EpistemicSnapshot.from_mapping(data[name])
        assert snapshot.content_hash == data[name]["content_hash"]
        assert snapshot.schema_version == "propstore.epistemic_snapshot.v2"
        assert snapshot.state.inventory is None
        assert snapshot.to_dict() == data[name]
    journal = _journal(data)
    assert journal.check_chain_integrity().ok
    assert to_document_builtins(journal) == data["journal"]
    worldline = convert_document_value(
        data["worldline"], WorldlineDefinition, source="frozen worldline"
    )
    assert worldline.journal == journal
    assert worldline.results is not None and worldline.results.revision is not None
    assert worldline.results.revision.state == EpistemicSnapshot.from_mapping(data["final_snapshot"])


def test_complete_original_journal_migrates_with_new_outcomes_and_hashes() -> None:
    data = _fixture()
    original = _journal(data)
    migrated = original.migrate()
    assert migrated.schema_version == "propstore.transition_journal.v6"
    assert all(entry.schema_version == migrated.schema_version for entry in migrated.entries)
    assert migrated.check_chain_integrity().ok
    assert migrated.replay().ok
    final = migrated.entries[-1].state_out
    assert final.schema_version == "propstore.epistemic_snapshot.v3"
    assert set(final.state.accepted_atom_ids) == {"assumption:a", "assumption:c", "assumption:d"}
    assert set(original.entries[-1].state_out.state.accepted_atom_ids) == {"assumption:c", "assumption:d"}
    restored_a = next(atom for atom in final.state.base.atoms if atom.atom_id == "assumption:a")
    assert isinstance(restored_a, AssumptionAtom)
    assert restored_a.assumption.source == "original-source-a"
    assert final.content_hash != data["final_snapshot"]["content_hash"]
    assert final == EpistemicSnapshot.from_mapping(data["final_snapshot"]).migrate(journal=original)
    restored = convert_document_value(
        to_document_builtins(migrated), TransitionJournal, source="migrated journal"
    )
    assert restored.check_chain_integrity().ok and restored.replay().ok
    assert to_document_builtins(original) == data["journal"]
    assert not original.replay().ok
    assert "migrate().replay()" in original.replay().errors[0]


def test_original_empty_history_seed_can_migrate_or_continue() -> None:
    data = _fixture()
    original = EpistemicSnapshot.from_mapping(data["initial_snapshot"])
    migrated = original.migrate()
    assert migrated.schema_version == "propstore.epistemic_snapshot.v3"
    assert migrated.state.inventory == original.state.base
    assert migrated.state.initial_atom_ids == ("assumption:a", "assumption:b")
    incoming = _journal(data).entries[0].operator_input.formula
    _, continued = iterated_revise(
        original.state, incoming, conflicts={incoming.atom_id: ("assumption:a",)},
        operator="lexicographic", max_candidates=8,
    )
    assert continued.inventory is not None
    assert continued.initial_atom_ids == migrated.state.initial_atom_ids


def test_missing_original_evidence_is_explicit_without_fabricating_history() -> None:
    data = _fixture()
    snapshot = EpistemicSnapshot.from_mapping(data["final_snapshot"])
    journal = _journal(data)
    with pytest.raises(RevisionContinuationUnavailable, match="complete original"):
        snapshot.migrate()
    with pytest.raises(RevisionContinuationUnavailable, match="complete original"):
        replace(journal, entries=journal.entries[1:]).migrate()
    with pytest.raises(RevisionContinuationUnavailable, match="original seed"):
        iterated_revise(snapshot.state, "assumption:c", max_candidates=8)
    assert snapshot.state.inventory is None
    assert snapshot.to_dict() == data["final_snapshot"]
    broken = replace(journal, entries=(journal.entries[0], journal.entries[0]))
    with pytest.raises(ValueError, match="broken journal"):
        broken.migrate()
    with pytest.raises(ValueError, match="broken journal"):
        snapshot.migrate(journal=broken)


def test_legacy_hash_validation_is_not_bypassed() -> None:
    data = _fixture()
    data["final_snapshot"]["state"]["accepted_atom_ids"] = []
    with pytest.raises(ValueError, match="content_hash"):
        EpistemicSnapshot.from_mapping(data["final_snapshot"])


@pytest.mark.parametrize("name", ("initial_snapshot", "final_snapshot"))
def test_legacy_identity_diff_preserves_version_hash_and_missing_evidence(name: str) -> None:
    source = EpistemicSnapshot.from_mapping(_fixture()[name])
    diff = diff_epistemic_snapshots(source, source)
    assert diff.deltas == ()
    applied = apply_epistemic_diff(source, diff)
    assert applied.to_dict() == source.to_dict()
    assert applied.content_hash == source.content_hash
    assert applied.schema_version == "propstore.epistemic_snapshot.v2"
    assert applied.state.inventory is None and applied.state.initial_atom_ids is None


@pytest.mark.parametrize("name", ("initial_snapshot", "final_snapshot"))
def test_legacy_nonempty_compatible_diff_preserves_version_and_target_hash(name: str) -> None:
    source = EpistemicSnapshot.from_mapping(_fixture()[name])
    # Ranking is an existing semantic-diff surface. Change the atom order in a
    # typed v2 target without supplying any lost continuation evidence.
    atom_ids = tuple(reversed(source.state.ranked_atom_ids))
    target = replace(source, content_hash="", state=replace(
        source.state,
        ranked_atom_ids=atom_ids,
        ranking={atom_id: index for index, atom_id in enumerate(atom_ids)},
    ))
    diff = diff_epistemic_snapshots(source, target)
    assert diff.deltas and all(delta.surface == "ranking" for delta in diff.deltas)
    assert target.content_hash != source.content_hash
    applied = apply_epistemic_diff(source, diff)
    assert applied.to_dict() == target.to_dict()
    assert applied.content_hash == diff.target_hash
    assert applied.schema_version == source.schema_version
    assert applied.state.inventory is None and applied.state.initial_atom_ids is None
