"""Property tests for ``snapshot_to_claim_ids`` — P1, P2, P3, P4.

These pin the projection contract from ``EpistemicSnapshot`` to the set
of sidecar ``claim_id`` strings that contributed source_claims to atoms
accepted in the snapshot. Per the design doc (section 11):

- P1: deterministic
- P2: empty snapshot maps to empty claim set
- P3: cid in result iff some accepted atom has it as a source_claim
- P4: many-to-one collapse — atom with N source_claims contributes all N
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.projection import snapshot_to_claim_ids
from tests.fixtures.journal import (
    empty_snapshot,
    make_assertion_atom,
    make_snapshot,
    make_state,
)


pytestmark = pytest.mark.property


# ---------- atom strategies ----------


@st.composite
def st_assertion_atom(draw, *, n_source_claims_min: int = 0, n_source_claims_max: int = 4):
    """Hypothesis strategy producing real ``AssertionAtom`` instances."""
    rel = draw(st.text(alphabet="abcdefghijklmnop", min_size=3, max_size=10))
    subj = draw(st.text(alphabet="abcdefghijklmnop", min_size=3, max_size=10))
    val = draw(st.text(alphabet="abcdefghijklmnop", min_size=3, max_size=10))
    n = draw(st.integers(min_value=n_source_claims_min, max_value=n_source_claims_max))
    locals_ = tuple(f"{rel}_{subj}_{val}_src_{i}" for i in range(n))
    return make_assertion_atom(
        relation_local=rel,
        subject=subj,
        value=val,
        source_claim_local_ids=locals_,
    )


@st.composite
def st_snapshot(draw, *, max_atoms: int = 5):
    """Snapshot with a mix of accepted and unaccepted atoms."""
    n_atoms = draw(st.integers(min_value=0, max_value=max_atoms))
    atoms_raw = []
    for i in range(n_atoms):
        atoms_raw.append(
            draw(
                st_assertion_atom(
                    n_source_claims_min=0, n_source_claims_max=3
                )
            )
        )
    # dedupe by atom_id (assertion identity is content-derived; collisions possible)
    seen: dict[str, object] = {}
    for atom in atoms_raw:
        seen.setdefault(atom.atom_id, atom)
    atoms = tuple(seen.values())
    if not atoms:
        return make_snapshot(make_state(atoms=(), accepted_atom_ids=()))
    accepted_count = draw(st.integers(min_value=0, max_value=len(atoms)))
    accepted_ids = tuple(a.atom_id for a in atoms[:accepted_count])
    state = make_state(atoms=atoms, accepted_atom_ids=accepted_ids)
    return make_snapshot(state)


@st.composite
def st_multi_source_snapshot(draw):
    """Snapshot guaranteed to contain at least one accepted atom with >=2 source_claims."""
    multi = draw(
        st_assertion_atom(n_source_claims_min=2, n_source_claims_max=4)
    )
    extras = draw(
        st.lists(
            st_assertion_atom(n_source_claims_min=0, n_source_claims_max=2),
            max_size=3,
        )
    )
    seen: dict[str, object] = {multi.atom_id: multi}
    for extra in extras:
        seen.setdefault(extra.atom_id, extra)
    atoms = tuple(seen.values())
    accepted_ids = tuple(a.atom_id for a in atoms)
    state = make_state(atoms=atoms, accepted_atom_ids=accepted_ids)
    return make_snapshot(state)


# ---------- properties ----------


@pytest.mark.property
@given(snap=st_snapshot())
@settings(deadline=None)
def test_p1_snapshot_to_claim_ids_deterministic(snap) -> None:
    assert snapshot_to_claim_ids(snap) == snapshot_to_claim_ids(snap)


def test_p2_empty_snapshot_yields_empty_set() -> None:
    assert snapshot_to_claim_ids(empty_snapshot()) == set()


@pytest.mark.property
@given(snap=st_snapshot())
@settings(deadline=None)
def test_p3_accepted_versus_unaccepted(snap) -> None:
    accepted = set(snap.state.accepted_atom_ids)
    result = snapshot_to_claim_ids(snap)
    expected = {
        str(claim.claim_id)
        for atom in snap.state.base.atoms
        if hasattr(atom, "source_claims") and atom.atom_id in accepted
        for claim in atom.source_claims
    }
    assert result == expected


@pytest.mark.property
@given(snap=st_multi_source_snapshot())
@settings(deadline=None)
def test_p4_many_to_one_collapse(snap) -> None:
    accepted = set(snap.state.accepted_atom_ids)
    expected = {
        str(claim.claim_id)
        for atom in snap.state.base.atoms
        if hasattr(atom, "source_claims") and atom.atom_id in accepted
        for claim in atom.source_claims
    }
    # Some accepted atom must carry >=2 source_claims for this strategy to be meaningful.
    multi_atoms = [
        atom
        for atom in snap.state.base.atoms
        if atom.atom_id in accepted
        and hasattr(atom, "source_claims")
        and len(atom.source_claims) >= 2
    ]
    assert multi_atoms, "strategy must guarantee a multi-source accepted atom"
    assert snapshot_to_claim_ids(snap) == expected
