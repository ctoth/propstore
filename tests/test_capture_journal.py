"""Worldline journal-capture tests.

The in-memory ``capture_journal`` surface, the ``at_journal_step`` bridge over a
captured journal, and the **document-codec round-trip** (a captured journal
survives ``Repository``-backed worldline persist -> load with the journal intact)
are exercised here. The worldline is a single canonical charter
(:class:`WorldlineDefinition`) that stores the journal as its canonical package
type (:class:`TransitionJournal`); Quire's codec owns the encode/decode, so there
is no mirror document, no ``to_document`` coercer, and no local mapping codec.
The ``cli.worldline`` cases still ride on the deferred CLI/owner surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.families.registry import WorldlineRef
from propstore.repository import Repository
from propstore.support_revision.history import JournalOperator, TransitionJournal
from propstore.support_revision.state import EpistemicState
from propstore.world.bridge import at_journal_step
from propstore.worldline.definition import WorldlineDefinition
from propstore.worldline.query import WorldlineRevisionQuery
from propstore.worldline.revision_types import RevisionAtomRef
from tests.fixtures.journal import (
    direct_dispatch,
    make_assertion_atom,
    make_state,
    synthetic_belief_space_with,
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


def _query_for(atom_id: str) -> WorldlineRevisionQuery:
    return WorldlineRevisionQuery(
        operation="revise",
        atom=RevisionAtomRef(kind="assertion", assertion_id=atom_id),
    )


def _contract_query_for(atom_id: str) -> WorldlineRevisionQuery:
    return WorldlineRevisionQuery(operation="contract", target=atom_id)


def _expand_query_for(atom_id: str) -> WorldlineRevisionQuery:
    return WorldlineRevisionQuery(
        operation="expand",
        atom=RevisionAtomRef(kind="assertion", assertion_id=atom_id),
    )


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
@settings(deadline=None)
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


def test_at_journal_step_matches_direct_dispatch_over_capture_journal() -> None:
    """Dixon P5 over a captured journal: the bridge's projected claim ids equal
    those of a real step-by-step re-dispatch (``direct_dispatch``), never a read
    of ``state_out``.
    """
    from propstore.worldline.revision_capture import capture_journal

    first = make_assertion_atom(
        relation_local="ajs_rel_1",
        subject="ajs_subject_1",
        value="ajs_value_1",
        source_claim_local_ids=("ajs_claim_1",),
    )
    second = make_assertion_atom(
        relation_local="ajs_rel_2",
        subject="ajs_subject_2",
        value="ajs_value_2",
        source_claim_local_ids=("ajs_claim_2",),
    )
    initial_state = make_state(atoms=(first, second), accepted_atom_ids=())
    journal = capture_journal(
        _JournalBound(initial_state),
        (_query_for(first.atom_id), _query_for(second.atom_id)),
    )
    space = synthetic_belief_space_with(first, second)

    for k in range(len(journal.entries)):
        ground_state = direct_dispatch(journal, k)
        accepted = set(ground_state.accepted_atom_ids)
        expected = {
            str(claim.claim_id)
            for atom in ground_state.base.atoms
            if atom.atom_id in accepted and hasattr(atom, "source_claims")
            for claim in atom.source_claims
        }
        assert at_journal_step(space, journal, k).claim_ids() == expected


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


def _capture_two_step_journal() -> TransitionJournal:
    first = make_assertion_atom(
        relation_local="doc_rel_1",
        subject="doc_subject_1",
        value="doc_value_1",
        source_claim_local_ids=("doc_claim_1",),
    )
    second = make_assertion_atom(
        relation_local="doc_rel_2",
        subject="doc_subject_2",
        value="doc_value_2",
        source_claim_local_ids=("doc_claim_2",),
    )
    initial_state = make_state(atoms=(first, second), accepted_atom_ids=())
    from propstore.worldline.revision_capture import capture_journal

    return capture_journal(
        _JournalBound(initial_state),
        (_query_for(first.atom_id), _query_for(second.atom_id)),
    )


def test_worldline_charter_journal_survives_repository_round_trip(tmp_path: Path) -> None:
    """A captured journal attached to a worldline survives persist -> load intact.

    The charter carries the journal as its canonical package type and Quire
    decodes it back. No mirror document, no local codec, no dict hop.
    """

    journal = _capture_two_step_journal()
    repo = Repository.init(tmp_path / "knowledge")
    definition = WorldlineDefinition(
        name="journalled",
        id="journalled",
        targets=["target"],
        journal=journal,
    )

    repo.families.worldlines.save(
        WorldlineRef("journalled"), definition, message="capture journal"
    )
    loaded = repo.families.worldlines.load(WorldlineRef("journalled"))

    assert loaded is not None
    reconstructed = loaded.journal
    assert isinstance(reconstructed, TransitionJournal)
    assert reconstructed == journal
    assert tuple(entry.content_hash for entry in reconstructed.entries) == tuple(
        entry.content_hash for entry in journal.entries
    )


def test_worldline_charter_journal_survives_quire_codec() -> None:
    """Quire's charter codec preserves the journal without a local codec."""

    journal = _capture_two_step_journal()
    definition = WorldlineDefinition(
        name="mapped", id="mapped", targets=["target"], journal=journal
    )

    codec = WorldlineDefinition.__charter__.document_codec()
    rebuilt = codec.decode(
        codec.encode(definition),
        WorldlineDefinition,
        source="test worldline journal",
    )

    assert rebuilt.journal == journal


def test_worldline_without_journal_loads_as_none(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    definition = WorldlineDefinition(name="plain", id="plain", targets=["target"])

    repo.families.worldlines.save(WorldlineRef("plain"), definition, message="no journal")
    loaded = repo.families.worldlines.load(WorldlineRef("plain"))

    assert loaded is not None
    assert loaded.journal is None


# ---------------------------------------------------------------------------
# Owner-layer journal cases: build_worldline_journal + worldline_at_step drive
# propstore.app.worldlines over a real Repository (not the CLI).


def _repo_with_one_atom(tmp_path: Path) -> tuple[Repository, str]:
    """A repo with one parameter claim; returns (repo, its projected atom id)."""
    from propstore.core.environment import Environment
    from propstore.families.claims import Claim, ClaimType
    from propstore.families.concepts import Concept
    from propstore.families.contexts import Context
    from propstore.world import WorldQuery

    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=10.0,
        ),
        message="m",
    )
    world = WorldQuery(repo)
    try:
        atoms = world.bind(Environment()).epistemic_state().base.atoms
    finally:
        world.close()
    assert atoms, "expected the single parameter claim to project to one atom"
    return repo, atoms[0].atom_id


def test_owner_build_worldline_journal_and_at_step_round_trip(tmp_path: Path) -> None:
    from propstore.app.worldlines import (
        WorldlineAtStepRequest,
        WorldlineBuildJournalRequest,
        build_worldline_journal,
        worldline_at_step,
    )

    repo, atom_id = _repo_with_one_atom(tmp_path)
    definition = WorldlineDefinition(
        id="wl",
        name="wl",
        targets=["Speed"],
        revision=WorldlineRevisionQuery(
            operation="revise",
            atom=RevisionAtomRef(kind="assertion", assertion_id=atom_id),
        ),
    )
    repo.families.worldlines.save(WorldlineRef("wl"), definition, message="seed")

    journal_report = build_worldline_journal(
        repo, WorldlineBuildJournalRequest(name="wl")
    )
    assert journal_report.step_count == 1

    # The journal was persisted on the charter and reconstructs to the package type.
    loaded = repo.families.worldlines.load(WorldlineRef("wl"))
    assert loaded is not None
    reconstructed = loaded.journal
    assert isinstance(reconstructed, TransitionJournal)
    assert len(reconstructed.entries) == 1

    step_report = worldline_at_step(repo, WorldlineAtStepRequest(name="wl", step=0))
    assert step_report.step == 0
    assert "cl1" in step_report.claim_ids


def test_owner_build_journal_without_revision_is_a_validation_error(
    tmp_path: Path,
) -> None:
    from propstore.app.worldlines import (
        WorldlineBuildJournalRequest,
        WorldlineValidationError,
        build_worldline_journal,
    )

    repo = Repository.init(tmp_path / "knowledge")
    repo.families.worldlines.save(
        WorldlineRef("wl"),
        WorldlineDefinition(name="wl", id="wl", targets=["Speed"]),
        message="no revision",
    )
    with pytest.raises(WorldlineValidationError):
        build_worldline_journal(repo, WorldlineBuildJournalRequest(name="wl"))


def test_owner_at_step_without_journal_is_a_validation_error(tmp_path: Path) -> None:
    from propstore.app.worldlines import (
        WorldlineAtStepRequest,
        WorldlineValidationError,
        worldline_at_step,
    )

    repo = Repository.init(tmp_path / "knowledge")
    repo.families.worldlines.save(
        WorldlineRef("wl"),
        WorldlineDefinition(name="wl", id="wl", targets=["Speed"]),
        message="no journal",
    )
    with pytest.raises(WorldlineValidationError):
        worldline_at_step(repo, WorldlineAtStepRequest(name="wl", step=0))


# ---------------------------------------------------------------------------
# CLI journal cases: `pks worldline build-journal` / `at-step` drive the thin
# propstore.cli.worldline adapter over the same owner surface (slice W3).


def test_cli_build_journal_and_at_step_round_trip(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from propstore.cli import cli

    repo, atom_id = _repo_with_one_atom(tmp_path)
    definition = WorldlineDefinition(
        id="wl",
        name="wl",
        targets=["Speed"],
        revision=WorldlineRevisionQuery(
            operation="revise",
            atom=RevisionAtomRef(kind="assertion", assertion_id=atom_id),
        ),
    )
    repo.families.worldlines.save(WorldlineRef("wl"), definition, message="seed")

    runner = CliRunner()
    built = runner.invoke(
        cli, ["-C", str(repo.root), "worldline", "build-journal", "wl"]
    )
    assert built.exit_code == 0, built.output
    assert "1 steps" in built.output

    at_step = runner.invoke(
        cli, ["-C", str(repo.root), "worldline", "at-step", "wl", "0"]
    )
    assert at_step.exit_code == 0, at_step.output
    assert "cl1" in at_step.output


def test_cli_at_step_without_journal_is_nonzero(tmp_path: Path) -> None:
    from click.testing import CliRunner

    from propstore.cli import cli

    repo = Repository.init(tmp_path / "knowledge")
    repo.families.worldlines.save(
        WorldlineRef("wl"),
        WorldlineDefinition(name="wl", id="wl", targets=["Speed"]),
        message="no journal",
    )
    result = CliRunner().invoke(
        cli, ["-C", str(repo.root), "worldline", "at-step", "wl", "0"]
    )
    assert result.exit_code != 0
    assert "journal" in result.output.lower()
