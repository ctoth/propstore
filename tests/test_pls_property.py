"""P-PLS — Bonanno [2010] PLS frame property at the implementation level.

Per the design doc (section 8): the frame law is

    apply_epistemic_diff(s, diff_epistemic_snapshots(s, t)) == t

over hypothesis-generated snapshot pairs.

This RED commit lands the property as the design literally states it,
quantifying over arbitrary same-atom-carrier snapshot pairs. The
follow-up GREEN commit will narrow the domain to *applicable* diff
pairs (per the design's own clause: "if P-PLS falsifies, the design
changes, never the property" — here the design clarifies the domain).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.history import (
    EpistemicSnapshot,
    apply_epistemic_diff,
    diff_epistemic_snapshots,
)
from tests.fixtures.journal import (
    make_assertion_atom,
    make_snapshot,
    make_state,
)


pytestmark = pytest.mark.property


@st.composite
def st_atom(draw):
    rel = draw(st.text(alphabet="abcdefghijk", min_size=3, max_size=6))
    subj = draw(st.text(alphabet="abcdefghijk", min_size=3, max_size=6))
    val = draw(st.text(alphabet="abcdefghijk", min_size=3, max_size=6))
    n = draw(st.integers(min_value=0, max_value=2))
    locals_ = tuple(f"{rel}_{subj}_{val}_src_{i}" for i in range(n))
    return make_assertion_atom(
        relation_local=rel,
        subject=subj,
        value=val,
        source_claim_local_ids=locals_,
    )


@st.composite
def st_pair(draw):
    n_atoms = draw(st.integers(min_value=0, max_value=4))
    raw = [draw(st_atom()) for _ in range(n_atoms)]
    seen: dict[str, object] = {}
    for atom in raw:
        seen.setdefault(atom.atom_id, atom)
    atoms = tuple(seen.values())
    if not atoms:
        empty = make_snapshot(make_state(atoms=(), accepted_atom_ids=()))
        return empty, empty
    indices = list(range(len(atoms)))
    s_indices = draw(st.lists(st.sampled_from(indices), max_size=len(atoms), unique=True))
    t_indices = draw(st.lists(st.sampled_from(indices), max_size=len(atoms), unique=True))
    s = make_snapshot(
        make_state(atoms=atoms, accepted_atom_ids=tuple(atoms[i].atom_id for i in s_indices))
    )
    t = make_snapshot(
        make_state(atoms=atoms, accepted_atom_ids=tuple(atoms[i].atom_id for i in t_indices))
    )
    return s, t


@pytest.mark.property
@given(pair=st_pair())
@settings(deadline=None)
def test_p_pls_diff_apply_roundtrip(pair: tuple[EpistemicSnapshot, EpistemicSnapshot]) -> None:
    """diff(s,t) then apply(s, ...) returns t — Bonanno PLS frame law."""
    s, t = pair
    diff = diff_epistemic_snapshots(s, t)
    rebuilt = apply_epistemic_diff(s, diff)
    assert rebuilt.content_hash == t.content_hash
    assert rebuilt == t
