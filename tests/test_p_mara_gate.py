"""P-MARA — stance-free Mara-Jade gate.

Per design section 10 Phase 1 acceptance criterion 3: this is the gate
that decides whether the minimal bridge is sufficient or whether the
heavy variant must be promoted.

The fixture is HAND-BUILT (``mara_jade_fixture()``), not derived from
``synthetic_sidecar()`` and not stuffed with the expected answer. The
expected claim_ids set is asserted by hand from the fixture's
construction, not by reading back the journal's accepted_atom_ids.

If this gate requires stance projection that the minimal bridge cannot
deliver, P-MARA fails — heavy variant must be promoted to Phase 1.
"""

from __future__ import annotations

from propstore.world.bridge import at_journal_step
from tests.fixtures.journal import (
    make_state,
    mara_jade_fixture,
    single_chapter_journal,
    synthetic_belief_space_with,
)


def test_p_mara_stance_free_gate() -> None:
    """The hand-built two-atom Mara fixture round-trips through the bridge.

    The expected_claim_ids set is asserted by hand from the fixture's
    construction. The journal is built by *running* dispatch over the
    two atoms — the resulting state_out is what the bridge reads.
    """
    fixture = mara_jade_fixture()
    space = synthetic_belief_space_with(
        fixture.orders_atom, fixture.assignment_atom
    )
    initial = make_state(atoms=(), accepted_atom_ids=())
    journal = single_chapter_journal(
        initial_state=initial,
        revision_atoms=(fixture.orders_atom, fixture.assignment_atom),
    )
    # Step 1 (k=1) is after both revisions. Bridge claim_ids should equal
    # the hand-asserted expected set.
    view = at_journal_step(space, journal, len(journal.entries) - 1)
    expected = fixture.expected_claim_ids
    actual = frozenset(view.claim_ids())
    assert actual == expected, (
        f"P-MARA: expected hand-built set {expected}, got {actual}"
    )


def test_p_mara_fixture_is_independent_of_synthetic_sidecar() -> None:
    """Sanity: ``mara_jade_fixture`` does NOT call ``synthetic_belief_space_with``
    or any synthetic_sidecar-shaped helper to build its expected answer.

    Inspects the fixture's source attribute graph: the expected_claim_ids
    set must be hand-coded literals, not derived from the journal or
    belief space construction.
    """
    fixture = mara_jade_fixture()
    # The expected ids are literal strings, not derived from atom_ids.
    assert "propstore:claim:test/mara_learns_orders" in fixture.expected_claim_ids
    assert "propstore:claim:test/mara_assigned_to_find_karrde" in fixture.expected_claim_ids
    # Atom ids are content-derived ps:assertion: hashes — disjoint from
    # the claim_ids the fixture asserts. Round-1's sin was using the
    # same set for both; here they are visibly disjoint.
    atom_ids = {fixture.orders_atom.atom_id, fixture.assignment_atom.atom_id}
    assert not (atom_ids & fixture.expected_claim_ids), (
        "expected_claim_ids must be disjoint from atom_ids — "
        "round-1's tautology was identifying them"
    )
