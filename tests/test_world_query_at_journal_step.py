"""Property tests for ``WorldQuery.at_journal_step`` and the bridge core.

Properties covered here:
- P5: Dixon-shape behavioural equivalence between ``at_journal_step`` and
  direct re-execution of the journal via ``support_revision.dispatch``.
- P6: step-bounds validation — IndexError on out-of-range step.

The synthetic belief space is a *real* protocol implementation
(SyntheticBeliefSpace in tests/fixtures/journal.py). It has real
``claims_by_ids`` and ``bind_for_view`` — no silent no-ops.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.world.bridge import at_journal_step  # NEW — introduced by GREEN
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


@pytest.mark.property
@given(triple=st_journal())
@settings(deadline=None)
def test_p6_step_bounds(triple) -> None:
    space, journal = triple
    with pytest.raises(IndexError):
        at_journal_step(space, journal, -1)
    with pytest.raises(IndexError):
        at_journal_step(space, journal, len(journal.entries))


# ---------- P5 — Dixon-shape behavioural equivalence ----------


@pytest.mark.property
@given(triple=st_journal())
@settings(deadline=None)
def test_p5_at_journal_step_matches_direct_dispatch(triple) -> None:
    """P5: at_journal_step's claim_ids equal those derived from a real
    re-dispatch of the journal up to step k.

    The oracle (``direct_dispatch``) calls
    ``support_revision.dispatch.dispatch`` for every step, threading the
    actual dispatched state forward. It does NOT read
    ``journal.entries[k].state_out`` (the round-1 sin).
    """
    space, journal = triple
    for k in range(len(journal.entries)):
        ground_state = direct_dispatch(journal, k)
        ground_truth_claim_ids = {
            str(claim.claim_id)
            for atom in ground_state.base.atoms
            if atom.atom_id in set(ground_state.accepted_atom_ids)
            and hasattr(atom, "source_claims")
            for claim in atom.source_claims
        }
        # Sanity check: the oracle path uses dispatch, the SUT uses snapshot_to_claim_ids
        # over the journal entry's state_out. They MUST agree on the claim-id set.
        view = at_journal_step(space, journal, k)
        assert view.claim_ids() == ground_truth_claim_ids, (
            f"step {k}: oracle={ground_truth_claim_ids}, "
            f"bridge={view.claim_ids()}, "
            f"missing={ground_truth_claim_ids - view.claim_ids()}, "
            f"extra={view.claim_ids() - ground_truth_claim_ids}"
        )


def test_p5_oracle_actually_calls_dispatch(monkeypatch) -> None:
    """Sanity gate against round-1's tautological-oracle sin.

    Patches ``propstore.support_revision.dispatch.dispatch`` to a tracker
    and confirms ``direct_dispatch`` invokes it for every journal step.
    If anyone removes the dispatch call and reads state_out instead, this
    test fails immediately.
    """
    from propstore.support_revision import dispatch as dispatch_mod

    real_dispatch = dispatch_mod.dispatch
    call_count = {"n": 0}

    def tracking_dispatch(*args, **kwargs):
        call_count["n"] += 1
        return real_dispatch(*args, **kwargs)

    # Patch BOTH the module-level binding and the binding the fixtures imported
    # at module import time.
    monkeypatch.setattr(dispatch_mod, "dispatch", tracking_dispatch)
    from tests.fixtures import journal as journal_fixtures

    monkeypatch.setattr(journal_fixtures, "dispatch", tracking_dispatch)

    atom_a = make_assertion_atom(
        relation_local="r1",
        subject="s",
        value="va",
        source_claim_local_ids=("c_a",),
    )
    atom_b = make_assertion_atom(
        relation_local="r2",
        subject="s",
        value="vb",
        source_claim_local_ids=("c_b",),
    )
    initial = make_state(atoms=(), accepted_atom_ids=())
    journal = single_chapter_journal(
        initial_state=initial, revision_atoms=(atom_a, atom_b)
    )
    # Construction itself uses dispatch (single_chapter_journal). Reset.
    construction_calls = call_count["n"]
    assert construction_calls >= 2

    # Now invoke the oracle and check it dispatches step+1 times.
    call_count["n"] = 0
    _ = direct_dispatch(journal, 0)
    assert call_count["n"] == 1, "direct_dispatch(j,0) must dispatch exactly once"

    call_count["n"] = 0
    _ = direct_dispatch(journal, 1)
    assert call_count["n"] == 2, "direct_dispatch(j,1) must dispatch exactly twice"
