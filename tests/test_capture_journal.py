from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner
from hypothesis import given
from hypothesis import strategies as st
import msgspec

from quire.documents import decode_document_bytes
from propstore.families.documents.worldlines import WorldlineDefinitionDocument
from propstore.families.registry import WorldlineRef
from propstore.support_revision.history import JournalOperator, TransitionJournal
from propstore.support_revision.state import EpistemicState
from propstore.worldline import WorldlineDefinition
from propstore.worldline.definition import WorldlineRevisionQuery
from tests.fixtures.journal import (
    direct_dispatch,
    make_assertion_atom,
    make_state,
    single_chapter_journal,
)


@dataclass(frozen=True)
class _JournalBound:
    initial_state: EpistemicState

    def epistemic_state(self) -> EpistemicState:
        return self.initial_state


class _JournalWorld:
    def __init__(self, bound: _JournalBound) -> None:
        self._bound = bound

    def bind(self, environment=None, *, policy=None, **conditions):
        return self._bound


class _WorldlineFamilyStore:
    def __init__(self, definition: WorldlineDefinition) -> None:
        self.saved: dict[str, object] = {definition.id: definition.to_document()}

    def load(self, ref: WorldlineRef):
        return self.saved.get(ref.name)

    def save(self, ref: WorldlineRef, document, *, message: str):
        self.saved[ref.name] = document
        return "commit:journal"


class _WorldlineFamilies:
    def __init__(self, definition: WorldlineDefinition) -> None:
        self.worldlines = _WorldlineFamilyStore(definition)


class _WorldlineRepo:
    def __init__(self, definition: WorldlineDefinition) -> None:
        self.families = _WorldlineFamilies(definition)


def _query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "revise",
        "atom": {"kind": "assertion", "id": atom_id},
        "conflicts": {},
    })
    assert query is not None
    return query


def _contract_query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "contract",
        "target": atom_id,
    })
    assert query is not None
    return query


def _expand_query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "expand",
        "atom": {"kind": "assertion", "id": atom_id},
    })
    assert query is not None
    return query


@st.composite
def _journal_inputs(draw):
    count = draw(st.integers(min_value=1, max_value=5))
    atoms = tuple(
        make_assertion_atom(
            relation_local=f"capture_rel_{index}",
            subject=f"capture_subject_{index}",
            value=f"capture_value_{index}",
            source_claim_local_ids=(f"capture_claim_{index}",),
        )
        for index in range(count)
    )
    initial_state = make_state(atoms=atoms, accepted_atom_ids=())
    queries = tuple(_query_for(atom.atom_id) for atom in atoms)
    return _JournalBound(initial_state), queries


@pytest.mark.property
@given(data=_journal_inputs())
def test_p_cap_1_capture_journal_is_deterministic(data) -> None:
    from propstore.worldline.revision_capture import capture_journal

    bound, queries = data

    first = capture_journal(bound, queries)
    second = capture_journal(bound, queries)

    assert isinstance(first, TransitionJournal)
    assert first == second
    assert tuple(entry.content_hash for entry in first.entries) == tuple(
        entry.content_hash for entry in second.entries
    )


@pytest.mark.property
@given(data=_journal_inputs())
def test_p_cap_2_capture_replay_matches_direct_dispatch(data) -> None:
    from propstore.worldline.revision_capture import capture_journal

    bound, queries = data

    journal = capture_journal(bound, queries)
    replayed = journal.replay()
    direct = direct_dispatch(journal, len(journal.entries) - 1)

    assert replayed.ok
    assert not replayed.errors
    assert not replayed.divergences
    assert journal.entries[-1].normalized_state_out == direct.to_canonical_dict()


def test_p_cap_3_legacy_worldline_definition_roundtrips_without_journal() -> None:
    from propstore.worldline import WorldlineDefinition

    definition = WorldlineDefinition.from_dict({
        "id": "legacy_without_journal",
        "targets": ["target"],
    })

    document = definition.to_document()
    loaded = WorldlineDefinition.from_document(document)

    assert loaded.journal is None
    assert "journal" not in loaded.to_dict()


def test_p_cap_4_journal_bearing_worldline_definition_roundtrips() -> None:
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="document_rel",
        subject="document_subject",
        value="document_value",
        source_claim_local_ids=("document_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())
    query = _query_for(atom.atom_id)
    journal = capture_journal(_JournalBound(initial_state), (query,))

    definition = WorldlineDefinition.from_dict({
        "id": "journal_bearing",
        "targets": ["target"],
        "journal": journal.to_dict(),
    })

    document = definition.to_document()
    loaded = WorldlineDefinition.from_document(document)

    assert loaded.journal is not None
    assert loaded.journal == journal
    assert loaded.to_dict()["journal"] == journal.to_dict()


def test_p_cap_4_journal_document_roundtrips_through_yaml_codec() -> None:
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="yaml_rel",
        subject="yaml_subject",
        value="yaml_value",
        source_claim_local_ids=("yaml_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())
    journal = capture_journal(_JournalBound(initial_state), (_query_for(atom.atom_id),))
    definition = WorldlineDefinition.from_dict({
        "id": "journal_yaml",
        "targets": ["target"],
        "journal": journal.to_dict(),
    })

    encoded = msgspec.yaml.encode(definition.to_document())
    decoded = decode_document_bytes(
        encoded,
        WorldlineDefinitionDocument,
        source="journal_yaml.yaml",
    )
    loaded = WorldlineDefinition.from_document(decoded)

    assert loaded.journal == journal


def test_p_cap_5_build_journal_cli_matches_in_memory(monkeypatch) -> None:
    from propstore.cli.worldline.journal import worldline_build_journal
    from propstore.policies import policy_profile_from_render_policy
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="cli_build_rel",
        subject="cli_build_subject",
        value="cli_build_value",
        source_claim_local_ids=("cli_build_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())
    query = _query_for(atom.atom_id)
    definition = WorldlineDefinition.from_dict({
        "id": "cli_build",
        "targets": ["target"],
        "revision": query.to_dict(),
    })
    repo = _WorldlineRepo(definition)

    @contextmanager
    def _open_world(_repo):
        yield _JournalWorld(_JournalBound(initial_state))

    monkeypatch.setattr("propstore.app.worldlines.open_app_world_model", _open_world)

    result = CliRunner().invoke(
        worldline_build_journal,
        ["cli_build"],
        obj={"repo": repo},
    )

    assert result.exit_code == 0, result.output
    saved = WorldlineDefinition.from_document(repo.families.worldlines.saved["cli_build"])
    expected = capture_journal(
        _JournalBound(initial_state),
        (query,),
        policy_payload=policy_profile_from_render_policy(definition.policy).to_dict(),
    )
    assert saved.journal == expected


def test_p_cap_5_at_step_cli_matches_world_query_method(tmp_path: Path, monkeypatch) -> None:
    from propstore.cli.worldline.journal import worldline_at_step
    from tests.test_world_query_at_journal_step_method import (
        _claim_id,
        _world_query_for_claims,
    )

    atom = make_assertion_atom(
        relation_local="cli_step_rel",
        subject="cli_step_subject",
        value="cli_step_value",
        source_claim_local_ids=("cli_step_claim",),
    )
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=()),
        revision_atoms=(atom,),
    )
    definition = WorldlineDefinition.from_dict({
        "id": "cli_step",
        "targets": ["target"],
        "journal": journal.to_dict(),
    })
    repo = _WorldlineRepo(definition)
    world = _world_query_for_claims(tmp_path, _claim_id("cli_step_claim"))

    @contextmanager
    def _open_world(_repo):
        yield world

    monkeypatch.setattr("propstore.app.worldlines.open_app_world_model", _open_world)
    try:
        expected = sorted(world.at_journal_step(journal, 0).claim_ids())
        result = CliRunner().invoke(
            worldline_at_step,
            ["cli_step", "0"],
            obj={"repo": repo},
        )
    finally:
        world.close()

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == expected


def test_build_journal_cli_reports_invalid_revision_without_traceback(monkeypatch) -> None:
    from propstore.cli.worldline.journal import worldline_build_journal

    atom = make_assertion_atom(
        relation_local="invalid_rel",
        subject="invalid_subject",
        value="invalid_value",
        source_claim_local_ids=("invalid_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())
    definition = WorldlineDefinition.from_dict({
        "id": "invalid_revision",
        "targets": ["target"],
        "revision": {
            "operation": "unknown",
            "atom": {"kind": "assertion", "id": atom.atom_id},
        },
    })
    repo = _WorldlineRepo(definition)

    @contextmanager
    def _open_world(_repo):
        yield _JournalWorld(_JournalBound(initial_state))

    monkeypatch.setattr("propstore.app.worldlines.open_app_world_model", _open_world)

    result = CliRunner().invoke(
        worldline_build_journal,
        ["invalid_revision"],
        obj={"repo": repo},
    )

    assert result.exit_code != 0
    assert "Unknown revision operation" in result.output
    assert "Traceback" not in result.output


def test_at_step_cli_reports_out_of_range_step_without_traceback(monkeypatch) -> None:
    from propstore.cli.worldline.journal import worldline_at_step

    class _StepErrorWorld:
        def at_journal_step(self, journal, step, *, heavy=False):
            raise IndexError(f"step {step} out of range")

    definition = WorldlineDefinition.from_dict({
        "id": "bad_step",
        "targets": ["target"],
        "journal": TransitionJournal(entries=()).to_dict(),
    })
    repo = _WorldlineRepo(definition)

    @contextmanager
    def _open_world(_repo):
        yield _StepErrorWorld()

    monkeypatch.setattr("propstore.app.worldlines.open_app_world_model", _open_world)

    result = CliRunner().invoke(
        worldline_at_step,
        ["bad_step", "999"],
        obj={"repo": repo},
    )

    assert result.exit_code != 0
    assert "step 999 out of range" in result.output
    assert "Traceback" not in result.output


def test_phase2_acceptance_captures_revise_revise_contract_journal() -> None:
    from propstore.worldline.revision_capture import capture_journal

    first = make_assertion_atom(
        relation_local="rrc_rel_1",
        subject="rrc_subject_1",
        value="rrc_value_1",
        source_claim_local_ids=("rrc_claim_1",),
    )
    second = make_assertion_atom(
        relation_local="rrc_rel_2",
        subject="rrc_subject_2",
        value="rrc_value_2",
        source_claim_local_ids=("rrc_claim_2",),
    )
    initial_state = make_state(atoms=(first, second), accepted_atom_ids=())

    journal = capture_journal(
        _JournalBound(initial_state),
        (
            _query_for(first.atom_id),
            _query_for(second.atom_id),
            _contract_query_for(first.atom_id),
        ),
    )
    direct = direct_dispatch(journal, 2)

    assert len(journal.entries) == 3
    assert [entry.operation.name for entry in journal.entries] == [
        "revise",
        "revise",
        "contract",
    ]
    assert journal.check_chain_integrity().ok
    assert journal.replay().ok
    assert journal.entries[-1].normalized_state_out == direct.to_canonical_dict()
    assert first.atom_id not in journal.entries[-1].state_out.state.accepted_atom_ids


def test_capture_journal_preserves_expand_as_expand_operator() -> None:
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="expand_rel",
        subject="expand_subject",
        value="expand_value",
        source_claim_local_ids=("expand_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())

    journal = capture_journal(
        _JournalBound(initial_state),
        (_expand_query_for(atom.atom_id),),
    )

    assert len(journal.entries) == 1
    assert journal.entries[0].operation.name == "expand"
    assert journal.entries[0].operator is JournalOperator.EXPAND
    assert journal.replay().ok
    assert atom.atom_id in journal.entries[0].state_out.state.accepted_atom_ids
