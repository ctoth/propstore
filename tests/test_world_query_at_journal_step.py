"""Property tests for the journal-step bridge core (``world.bridge``).

Properties covered here:
- P5: Dixon-shape behavioural equivalence between ``at_journal_step`` and direct
  re-execution of the journal via ``support_revision.dispatch``.
- P6: step-bounds validation — IndexError on out-of-range step.
- heavy fixture path: the heavy variant surfaces registered stances/conflicts and
  caches by ``(commit, claim_ids)``.

The synthetic belief space is a *real* protocol implementation
(``SyntheticBeliefSpace`` in ``tests/fixtures/journal.py``). It has a real
``claims_by_ids`` — no silent no-ops.
"""

from __future__ import annotations

import pytest
from condition_ir import CelExpr
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.conflict_detector import ConflictClass
from propstore.conflict_detector.models import ConflictRecord
from propstore.families.relations import Stance
from propstore.stances import StanceType
from propstore.support_revision.state import RevisionScope
from propstore.world.bridge import at_journal_step
from propstore.world.journal_replay import cache_stats, register_fixture_commit, reset_cache
from tests.fixtures.journal import (
    direct_dispatch,
    make_assertion_atom,
    make_state,
    single_chapter_journal,
    synthetic_belief_space_with,
)

pytestmark = pytest.mark.property


@st.composite
def st_atom(draw, *, ix: int):
    rel = draw(st.text(alphabet="abcdefghi", min_size=3, max_size=6))
    subj = draw(st.text(alphabet="abcdefghi", min_size=3, max_size=6))
    val = draw(st.text(alphabet="abcdefghi", min_size=3, max_size=6))
    return make_assertion_atom(
        relation_local=f"{rel}_{ix}",
        subject=subj,
        value=val,
        source_claim_local_ids=(f"src_{rel}_{subj}_{val}_{ix}",),
    )


@st.composite
def st_journal(draw):
    n_steps = draw(st.integers(min_value=1, max_value=5))
    raw = [draw(st_atom(ix=i)) for i in range(n_steps)]
    seen: dict[str, object] = {}
    for atom in raw:
        seen.setdefault(atom.atom_id, atom)
    atoms = tuple(seen.values())
    if not atoms:
        atoms = (
            make_assertion_atom(
                relation_local="fallback_rel",
                subject="fallback_subj",
                value="fallback_val",
                source_claim_local_ids=("fallback_src",),
            ),
        )
    initial = make_state(atoms=(), accepted_atom_ids=())
    journal = single_chapter_journal(initial_state=initial, revision_atoms=atoms)
    space = synthetic_belief_space_with(*atoms)
    return space, journal


# ---------- P6 — step bounds ----------


@given(triple=st_journal())
@settings(deadline=None)
def test_p6_step_bounds(triple) -> None:
    space, journal = triple
    with pytest.raises(IndexError):
        at_journal_step(space, journal, -1)
    with pytest.raises(IndexError):
        at_journal_step(space, journal, len(journal.entries))


# ---------- P5 — Dixon-shape behavioural equivalence ----------


@given(triple=st_journal())
@settings(deadline=None)
def test_p5_at_journal_step_matches_direct_dispatch(triple) -> None:
    """P5: at_journal_step's claim_ids equal those derived from a real
    re-dispatch of the journal up to step k.

    The oracle (``direct_dispatch``) calls ``support_revision.dispatch.dispatch``
    for every step, threading the actual dispatched state forward. It does NOT
    read ``journal.entries[k].state_out``.
    """
    space, journal = triple
    for k in range(len(journal.entries)):
        ground_state = direct_dispatch(journal, k)
        accepted = set(ground_state.accepted_atom_ids)
        ground_truth_claim_ids = {
            str(claim.claim_id)
            for atom in ground_state.base.atoms
            if atom.atom_id in accepted and hasattr(atom, "source_claims")
            for claim in atom.source_claims
        }
        view = at_journal_step(space, journal, k)
        assert view.claim_ids() == ground_truth_claim_ids, (
            f"step {k}: oracle={ground_truth_claim_ids}, "
            f"bridge={view.claim_ids()}"
        )


def test_p5_oracle_actually_calls_dispatch(monkeypatch) -> None:
    """Sanity gate against a tautological oracle.

    Confirms ``direct_dispatch`` invokes ``dispatch`` once per journal step. If
    anyone removes the dispatch call and reads state_out instead, this fails.
    """
    from propstore.support_revision import dispatch as dispatch_mod

    real_dispatch = dispatch_mod.dispatch
    call_count = {"n": 0}

    def tracking_dispatch(*args, **kwargs):
        call_count["n"] += 1
        return real_dispatch(*args, **kwargs)

    monkeypatch.setattr(dispatch_mod, "dispatch", tracking_dispatch)
    from tests.fixtures import journal as journal_fixtures

    monkeypatch.setattr(journal_fixtures, "dispatch", tracking_dispatch)

    atom_a = make_assertion_atom(
        relation_local="r1", subject="s", value="va", source_claim_local_ids=("c_a",)
    )
    atom_b = make_assertion_atom(
        relation_local="r2", subject="s", value="vb", source_claim_local_ids=("c_b",)
    )
    initial = make_state(atoms=(), accepted_atom_ids=())
    journal = single_chapter_journal(
        initial_state=initial, revision_atoms=(atom_a, atom_b)
    )
    assert call_count["n"] >= 2  # construction itself dispatches

    call_count["n"] = 0
    _ = direct_dispatch(journal, 0)
    assert call_count["n"] == 1, "direct_dispatch(j,0) must dispatch exactly once"

    call_count["n"] = 0
    _ = direct_dispatch(journal, 1)
    assert call_count["n"] == 2, "direct_dispatch(j,1) must dispatch exactly twice"


# ---------- heavy fixture path ----------


def test_heavy_surfaces_registered_stances_and_conflicts() -> None:
    reset_cache()
    claim_a = "propstore:claim:test/heavy_a"
    claim_b = "propstore:claim:test/heavy_b"
    atom_a = make_assertion_atom(
        relation_local="hv1",
        subject="s",
        value="va",
        source_claim_ids=(claim_a,),
    )
    atom_b = make_assertion_atom(
        relation_local="hv2",
        subject="s",
        value="vb",
        source_claim_ids=(claim_b,),
    )
    commit = "a" * 40
    scope = RevisionScope(bindings={}, context_id=None, commit=commit)
    initial = make_state(atoms=(), accepted_atom_ids=(), scope=scope)
    journal = single_chapter_journal(
        initial_state=initial, revision_atoms=(atom_a, atom_b)
    )
    space = synthetic_belief_space_with(atom_a, atom_b)

    stance = Stance(
        stance_id="hv_stance",
        source_claim_id=claim_a,
        target_claim_id=claim_b,
        stance_type=StanceType.SUPPORTS,
    )
    conflict = ConflictRecord(
        concept_id="concept:test",
        claim_a_id=claim_a,
        claim_b_id=claim_b,
        warning_class=ConflictClass.CONFLICT,
        conditions_a=list[CelExpr](),
        conditions_b=list[CelExpr](),
        value_a="va",
        value_b="vb",
    )
    register_fixture_commit(
        commit,
        claim_ids=frozenset({claim_a, claim_b}),
        stances=(stance,),
        conflicts=(conflict,),
    )

    view = at_journal_step(space, journal, 1, heavy=True)
    assert view.stances == (stance,)
    assert view.conflicts == (conflict,)
    assert {claim_a, claim_b} <= view.claim_ids()

    # A second heavy call at the same commit/claim-id set is a cache hit.
    before = cache_stats().hits
    _ = at_journal_step(space, journal, 1, heavy=True)
    assert cache_stats().hits == before + 1


def test_heavy_requires_commit_scope() -> None:
    atom = make_assertion_atom(
        relation_local="nocommit",
        subject="s",
        value="v",
        source_claim_local_ids=("nc",),
    )
    initial = make_state(atoms=(), accepted_atom_ids=())  # scope.commit is None
    journal = single_chapter_journal(initial_state=initial, revision_atoms=(atom,))
    space = synthetic_belief_space_with(atom)
    with pytest.raises(ValueError, match="commit"):
        at_journal_step(space, journal, 0, heavy=True)
