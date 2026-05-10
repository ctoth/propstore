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

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import cast

import pytest

from propstore.core.id_types import ClaimId, to_claim_id
from propstore.core.row_types import ConflictRow, StanceRow
from propstore.stances import StanceType
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
from propstore.support_revision.state import AssertionAtom, RevisionScope
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


@dataclass
class SyntheticHeavyBeliefSpace(SyntheticBeliefSpace):
    stance_rows: tuple[StanceRow, ...] = ()
    conflict_rows: tuple[ConflictRow, ...] = ()

    def all_claim_stances(self) -> list[StanceRow]:
        return list(self.stance_rows)

    def conflicts(self, concept_id: str | None = None) -> list[ConflictRow]:
        return list(self.conflict_rows)


class SyntheticHistoricalBeliefSpace(SyntheticBeliefSpace):
    def __init__(self, historical_space: SyntheticHeavyBeliefSpace) -> None:
        super().__init__()
        self.historical_space = historical_space
        self.requested_commits: list[str] = []

    @contextmanager
    def historical_query(
        self,
        commit_sha: str,
    ) -> Iterator[SyntheticHeavyBeliefSpace]:
        self.requested_commits.append(commit_sha)
        yield self.historical_space


def _claim_id(local_id: str) -> ClaimId:
    return to_claim_id(f"propstore:claim:test/{local_id}")


def _build_heavy_journal(*, atoms: tuple[AssertionAtom, ...], commit_sha: str):
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
        atoms=cast(tuple[AssertionAtom, ...], next_state.base.atoms),
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
    extra_row = space.add_claim("c2")
    fake_stance = StanceRow(
        claim_id=_claim_id("c1"),
        target_claim_id=extra_row.claim_id,
        stance_type=StanceType.SUPPORTS,
    )
    fake_conflict = ConflictRow(
        claim_a_id=_claim_id("c1"),
        claim_b_id=extra_row.claim_id,
    )
    register_fixture_commit(
        commit_sha,
        claim_ids=frozenset({str(extra_row.claim_id)}),
        stances=(fake_stance,),
        conflicts=(fake_conflict,),
    )
    journal = _build_heavy_journal(atoms=(atom,), commit_sha=commit_sha)

    light = at_journal_step(space, journal, 0, heavy=False)
    heavy = at_journal_step(space, journal, 0, heavy=True)
    assert light.stances == ()
    assert light.conflicts == ()
    assert heavy.stances == (fake_stance,)
    assert heavy.conflicts == (fake_conflict,)


def test_p_heavy_2b_unregistered_commit_derives_typed_rows_from_world_query_surface() -> None:
    """Heavy returns production stance/conflict rows for the accepted claim set."""
    atom = make_assertion_atom(
        relation_local="r",
        subject="s",
        value="v",
        source_claim_local_ids=("c1", "c2"),
    )
    base_space = synthetic_belief_space_with(atom)
    stance = StanceRow(
        claim_id=_claim_id("c1"),
        target_claim_id=_claim_id("c2"),
        stance_type=StanceType.REBUTS,
    )
    conflict = ConflictRow(
        claim_a_id=_claim_id("c1"),
        claim_b_id=_claim_id("c2"),
    )
    space = SyntheticHeavyBeliefSpace(
        rows=base_space.rows,
        stance_rows=(stance,),
        conflict_rows=(conflict,),
    )
    journal = _build_heavy_journal(atoms=(atom,), commit_sha="d" * 40)

    heavy = at_journal_step(space, journal, 0, heavy=True)
    assert heavy.claim_ids() == {str(_claim_id("c1")), str(_claim_id("c2"))}
    assert heavy.stances == (stance,)
    assert heavy.conflicts == (conflict,)


def test_p_heavy_2c_unregistered_commit_uses_historical_query_surface() -> None:
    """Repository-backed heavy replay reads the commit-scoped query surface."""
    from propstore.world import journal_replay

    atom = make_assertion_atom(
        relation_local="r",
        subject="s",
        value="v",
        source_claim_local_ids=("c1", "c2"),
    )
    base_space = synthetic_belief_space_with(atom)
    stance = StanceRow(
        claim_id=_claim_id("c1"),
        target_claim_id=_claim_id("c2"),
        stance_type=StanceType.SUPPORTS,
    )
    conflict = ConflictRow(
        claim_a_id=_claim_id("c1"),
        claim_b_id=_claim_id("c2"),
    )
    historical_space = SyntheticHeavyBeliefSpace(
        rows=base_space.rows,
        stance_rows=(stance,),
        conflict_rows=(conflict,),
    )
    space = SyntheticHistoricalBeliefSpace(historical_space)
    commit_sha = "e" * 40
    journal = _build_heavy_journal(atoms=(atom,), commit_sha=commit_sha)

    journal_replay.reset_cache()
    heavy = at_journal_step(space, journal, 0, heavy=True)
    assert space.requested_commits == [commit_sha]
    assert heavy.claim_ids() == {str(_claim_id("c1")), str(_claim_id("c2"))}
    assert heavy.stances == (stance,)
    assert heavy.conflicts == (conflict,)


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
