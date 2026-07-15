"""Production-method tests for ``WorldQuery.at_journal_step``.

These supplement the bridge free-function property tests by constructing a real
:class:`~propstore.world.model.WorldQuery` over a charter-backed sidecar (authored
via :meth:`Repository.init` + the families API, exactly as
``tests/test_worldline_world_query.py`` builds its reader) and invoking the public
method directly. No pre-charter ``family_helpers`` / ``build_world_projection_schema``
/ ``relation_edge`` shapes are used — the sidecar is the real charter projection.
"""

from __future__ import annotations

from pathlib import Path

from propstore.support_revision.integrity_constraints import (
    AtomConstraint,
    LiteralsConstraint,
    TopConstraint,
)
from propstore.support_revision.operator_inputs import (
    ContractInput,
    ExpandInput,
    ICMergeInput,
    IteratedReviseInput,
    ReviseInput,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionOperation,
)
from propstore.support_revision.state import RevisionScope
from propstore.world import WorldQuery
from propstore.world.journal_replay import reset_cache
from tests.fixtures.journal import (
    make_assertion_atom,
    make_journal_entry,
    make_state,
    single_chapter_journal,
)


def _atom(claim_id: str, ix: int):
    return make_assertion_atom(
        relation_local=f"method_rel_{ix}",
        subject=f"method_subject_{ix}",
        value=f"method_value_{ix}",
        source_claim_ids=(claim_id,),
    )


def _repo(tmp_path: Path, *claim_ids: str, rebut: bool = False) -> Repository:
    """Author a concept + context + one parameter claim per id, on one concept."""

    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    for seq, claim_id in enumerate(claim_ids):
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                context_id="ctx1",
                claim_type=ClaimType.PARAMETER,
                output_concept="c1",
                value=float(10 * (seq + 1)),
            ),
            message="m",
        )
    if rebut and len(claim_ids) >= 2:
        repo.families.stance.save(
            "s1",
            Stance(
                stance_id="s1",
                source_claim_id=claim_ids[0],
                target_claim_id=claim_ids[1],
                stance_type=StanceType.REBUTS,
                confidence=0.9,
            ),
            message="m",
        )
    return repo


def test_world_query_method_projects_single_step_journal(tmp_path: Path) -> None:
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=()),
        revision_atoms=(_atom("cl1", 1),),
    )
    world = WorldQuery(_repo(tmp_path, "cl1"))
    try:
        view = world.at_journal_step(journal, 0)
        assert view.claim_ids() == {"cl1"}
    finally:
        world.close()


def test_world_query_method_projects_intermediate_step(tmp_path: Path) -> None:
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=()),
        revision_atoms=(_atom("cl1", 1), _atom("cl2", 2), _atom("cl3", 3)),
    )
    world = WorldQuery(_repo(tmp_path, "cl1", "cl2", "cl3"))
    try:
        view = world.at_journal_step(journal, 1)
        assert view.claim_ids() == {"cl1", "cl2"}
    finally:
        world.close()


def test_world_query_method_projects_empty_acceptance_step(tmp_path: Path) -> None:
    atom = _atom("cl1", 1)
    state = make_state(atoms=(atom,), accepted_atom_ids=())
    entry = make_journal_entry(
        state_in=state,
        operation=TransitionOperation(
            name="contract",
            input_atom_id=None,
            target_atom_ids=(atom.atom_id,),
        ),
        operator=JournalOperator.CONTRACT,
        operator_input={"atom_id": atom.atom_id},
        state_out=state,
    )
    world = WorldQuery(_repo(tmp_path, "cl1"))
    try:
        view = world.at_journal_step(TransitionJournal(entries=(entry,)), 0)
        assert view.claim_ids() == set()
    finally:
        world.close()


def test_world_query_method_heavy_replay_populates_stances_and_conflicts(
    tmp_path: Path,
) -> None:
    reset_cache()
    repo = _repo(tmp_path, "cl1", "cl2", rebut=True)
    head = repo.git.head_sha()
    assert head is not None
    scope = RevisionScope(bindings={}, context_id=None, commit=head)
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=(), scope=scope),
        revision_atoms=(_atom("cl1", 1), _atom("cl2", 2)),
    )
    world = WorldQuery(repo)
    try:
        view = world.at_journal_step(journal, 1, heavy=True)
        assert view.claim_ids() == {"cl1", "cl2"}
        # The rebutting stance and the two-rival-values conflict fall within the
        # accepted claim set, so the heavy replay surfaces both.
        assert {
            (str(s.source_claim_id), str(s.target_claim_id)) for s in view.stances
        } == {("cl1", "cl2")}
        assert {
            (str(c.claim_a_id), str(c.claim_b_id)) for c in view.conflicts
        } == {("cl1", "cl2")}
    finally:
        world.close()
