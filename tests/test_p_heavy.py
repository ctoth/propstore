"""P-HEAVY-1/2/3 — heavy variant of at_journal_step.

Per design section 7 + 11 (Phase 3 properties):

- P-HEAVY-1: parity on stance-free input — heavy and minimal return the
  same claim_ids when no stances are involved.
- P-HEAVY-2: heavy surfaces stances minimal does not — when the
  underlying journal scope identifies stances, heavy returns them while
  minimal returns ().
- P-HEAVY-3: cache hits/misses are observable.

The heavy path requires ``snapshot.scope.commit`` (enforced by the
scope_policy require= rule). For property tests, the synthetic belief
space implements a minimal commit registry: scope.commit identifies a
named registered fixture; ``replay_at_step`` looks it up.
"""

from __future__ import annotations

import pytest

from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionOperation,
)
from propstore.support_revision.snapshot_types import (
    EpistemicStateSnapshot,
    belief_atom_to_canonical_dict,
)
from propstore.support_revision.state import RevisionScope
from propstore.world.bridge import at_journal_step
from propstore.world.journal_replay import (
    HeavyCacheStats,
    register_fixture_commit,
)
from tests.fixtures.journal import (
    SyntheticBeliefSpace,
    make_assertion_atom,
    make_journal_entry,
    make_state,
    synthetic_belief_space_with,
)


def _build_heavy_journal(*, atoms, commit_sha: str, stances: tuple = ()):
    """Build a 1-step journal whose state_out scope has commit=commit_sha."""
    state_in = make_state(atoms=(), accepted_atom_ids=())
    formula_atom = atoms[0]
    operator_input = {
        "formula": belief_atom_to_canonical_dict(formula_atom),
        "max_candidates": 8,
        "conflicts": {},
    }
    next_state = dispatch(
        JournalOperator.REVISE,
        state_in=EpistemicStateSnapshot.from_state(state_in).to_dict(),
        operator_input=operator_input,
        policy={
            "revision_policy_version": "v1",
            "ranking_policy_version": "v1",
            "entrenchment_policy_version": "v1",
        },
    )
    scope = RevisionScope(
        bindings={"k": "v"},
        context_id=None,
        branch="main",
        commit=commit_sha,
    )
    state_out = make_state(
        atoms=next_state.base.atoms,
        accepted_atom_ids=next_state.accepted_atom_ids,
        scope=scope,
    )
    operation = TransitionOperation(name="revise", input_atom_id=formula_atom.atom_id)
    entry = make_journal_entry(
        state_in=state_in,
        operation=operation,
        operator=JournalOperator.REVISE,
        operator_input=operator_input,
        state_out=state_out,
    )
    return TransitionJournal(entries=(entry,))


def test_p_heavy_1_parity_on_stance_free_input() -> None:
    """Heavy variant returns the same claim_ids as minimal on stance-free journals."""
    atom = make_assertion_atom(
        relation_local="r",
        subject="s",
        value="v",
        source_claim_local_ids=("c1",),
    )
    space = synthetic_belief_space_with(atom)
    commit_sha = "a" * 40
    register_fixture_commit(commit_sha, claim_ids=frozenset(), stances=())
    journal = _build_heavy_journal(atoms=(atom,), commit_sha=commit_sha)

    light = at_journal_step(space, journal, 0, heavy=False)
    heavy = at_journal_step(space, journal, 0, heavy=True)
    assert light.claim_ids() == heavy.claim_ids()


def test_p_heavy_2_heavy_surfaces_stances_minimal_does_not() -> None:
    """Heavy returns stances; minimal returns the empty tuple."""
    atom = make_assertion_atom(
        relation_local="r",
        subject="s",
        value="v",
        source_claim_local_ids=("c1",),
    )
    space = synthetic_belief_space_with(atom)
    commit_sha = "b" * 40
    # Pre-register a stance for this commit. The journal_replay module
    # surfaces it under heavy=True only.
    fake_stance = {"source": "c1", "target": "c2", "kind": "supports"}
    register_fixture_commit(commit_sha, claim_ids=frozenset(), stances=(fake_stance,))
    journal = _build_heavy_journal(atoms=(atom,), commit_sha=commit_sha)

    light = at_journal_step(space, journal, 0, heavy=False)
    heavy = at_journal_step(space, journal, 0, heavy=True)
    assert light.stances == ()
    assert heavy.stances == (fake_stance,)


def test_p_heavy_3_cache_hits_misses_are_observable() -> None:
    """Repeated heavy calls observe a cache hit; first call is a miss."""
    from propstore.world import journal_replay

    atom = make_assertion_atom(
        relation_local="r",
        subject="s",
        value="v",
        source_claim_local_ids=("c1",),
    )
    space = synthetic_belief_space_with(atom)
    commit_sha = "c" * 40
    register_fixture_commit(commit_sha, claim_ids=frozenset(), stances=())
    journal = _build_heavy_journal(atoms=(atom,), commit_sha=commit_sha)

    journal_replay.reset_cache()
    stats_before = journal_replay.cache_stats()
    assert stats_before == HeavyCacheStats(hits=0, misses=0, size=0)

    _ = at_journal_step(space, journal, 0, heavy=True)
    after_first = journal_replay.cache_stats()
    assert after_first.misses == 1
    assert after_first.hits == 0
    assert after_first.size == 1

    _ = at_journal_step(space, journal, 0, heavy=True)
    after_second = journal_replay.cache_stats()
    assert after_second.hits == 1
    assert after_second.misses == 1
    assert after_second.size == 1
