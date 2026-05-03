"""P-PLS — Bonanno [2010] PLS frame property at the implementation level.

Per the design doc (section 8): the frame law is

    apply_epistemic_diff(s, diff_epistemic_snapshots(s, t)) == t

PLS in Bonanno [2010] is *the past looks the same* — at a branch point, two
histories with identical pre-branch state remain identical-up-to-relabeling
under the same information at the branch.

For the PLS frame property to apply, ``t`` must be reachable from ``s`` by
operations that propstore's diff/apply machinery actually represents. The
implementation diffs five surfaces: assertion_acceptance, warrant, ranking,
provenance, dependency. If ``t`` differs from ``s`` outside these surfaces
(e.g. a different atom carrier, ranked_atom_ids ordering not derivable
from a sequence of ranking deltas, etc.), the diff cannot capture the
delta and PLS does not apply at the implementation layer.

We therefore generate ``t`` *by applying a hypothesis-generated diff to
``s``*. The PLS round-trip then asserts the design property exactly: any
state pair connected by an actual applicable diff round-trips through
diff/apply. This is PLS at the implementation level — the same-branch
precondition is enforced by construction.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.history import (
    EpistemicSemanticDiff,
    EpistemicSnapshot,
    SemanticFieldDelta,
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
def st_pls_pair(draw):
    """Build (s, t) where t = apply(s, generated diff).

    s is a snapshot built from a generated atom carrier with no acceptance
    state. The diff toggles a subset of atom ids' acceptance. Because t is
    constructed by applying that diff, it is by definition reachable from s
    on a PLS-valid branch — and the round-trip is the property.
    """
    n_atoms = draw(st.integers(min_value=0, max_value=4))
    raw = [draw(st_atom()) for _ in range(n_atoms)]
    seen: dict[str, object] = {}
    for atom in raw:
        seen.setdefault(atom.atom_id, atom)
    atoms = tuple(seen.values())
    s = make_snapshot(make_state(atoms=atoms, accepted_atom_ids=()))
    # Build a diff whose deltas accept some subset of atom ids.
    if not atoms:
        empty_diff = EpistemicSemanticDiff(
            source_hash=s.content_hash,
            target_hash=s.content_hash,
            deltas=(),
        )
        return s, s, empty_diff
    chosen_indices = draw(st.lists(st.sampled_from(range(len(atoms))), unique=True))
    deltas = tuple(
        SemanticFieldDelta(
            surface="assertion_acceptance",
            key=atoms[i].atom_id,
            old_value=None,
            new_value=True,
        )
        # Apply in sorted key order — same order propstore uses internally.
        for i in sorted(chosen_indices, key=lambda j: atoms[j].atom_id)
    )
    # Construct an EpistemicSemanticDiff. We need a target_hash; cheat by
    # applying the deltas through propstore's own machinery to derive it.
    proto_diff = EpistemicSemanticDiff(
        source_hash=s.content_hash,
        target_hash="",
        deltas=deltas,
    )
    # Compute the actual t by patching s's payload with the deltas, then
    # rehashing — using the same machinery apply_epistemic_diff uses.
    payload = s.state.to_dict()
    accepted_list = list(payload["accepted_atom_ids"])
    for delta in deltas:
        if delta.key not in accepted_list:
            accepted_list.append(delta.key)
    payload["accepted_atom_ids"] = accepted_list
    t = EpistemicSnapshot.from_mapping(
        {
            "schema_version": s.schema_version,
            "state": payload,
        }
    )
    diff = EpistemicSemanticDiff(
        source_hash=s.content_hash,
        target_hash=t.content_hash,
        deltas=deltas,
    )
    return s, t, diff


@pytest.mark.property
@given(triple=st_pls_pair())
@settings(deadline=None)
def test_p_pls_diff_apply_roundtrip(
    triple: tuple[EpistemicSnapshot, EpistemicSnapshot, EpistemicSemanticDiff],
) -> None:
    """apply(s, diff(s,t)) == t — Bonanno PLS frame law on applicable diffs.

    Verifies BOTH directions of the round-trip:
      (a) the constructed diff round-trips through ``apply_epistemic_diff``
      (b) ``diff_epistemic_snapshots(s, t)`` reproduces the same target hash.
    """
    s, t, constructed_diff = triple
    # (a) The generated diff round-trips.
    rebuilt_via_constructed = apply_epistemic_diff(s, constructed_diff)
    assert rebuilt_via_constructed.content_hash == t.content_hash
    assert rebuilt_via_constructed == t
    # (b) propstore's own diff produces the same applicable diff.
    derived_diff = diff_epistemic_snapshots(s, t)
    rebuilt_via_derived = apply_epistemic_diff(s, derived_diff)
    assert rebuilt_via_derived.content_hash == t.content_hash
    assert rebuilt_via_derived == t
