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
    apply_epistemic_diff,
    diff_epistemic_snapshots,
)
from tests.fixtures.journal import (
    make_assertion_atom,
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
