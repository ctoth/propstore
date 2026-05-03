"""Property tests for ``@scope_policy`` decorator + integration with at_journal_step.

Three properties from design section 11:
- P-SCOPE-DEGRADE: when ``rebind=True`` is requested but a degrade-required
  scope field is missing, emit UserWarning and force the kwarg to False.
- P-SCOPE-REQUIRE: when ``heavy=True`` is requested but a require-required
  scope field is missing, raise ValueError.
- P-SCOPE-NOOP: when scope is complete and ``rebind=True`` is requested,
  the call returns a ClaimView whose ``bound`` field is observably set
  (proves the rebind path actually rebound — not silently no-op'd).

The decorator's policy lives at module level (no test-imports leaking
into production); these tests reach the decorated method by calling
``at_journal_step`` against a synthetic belief space.
"""

from __future__ import annotations

import warnings

import pytest

from propstore.support_revision.state import RevisionScope
from propstore.world.bridge import at_journal_step
from tests.fixtures.journal import (
    make_assertion_atom,
    make_journal_entry,
    make_state,
    synthetic_belief_space_with,
)
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionOperation,
)
from propstore.support_revision.snapshot_types import (
    belief_atom_to_canonical_dict,
)
from propstore.support_revision.dispatch import dispatch


def _build_journal_with_scope(*, scope_in: RevisionScope, scope_out: RevisionScope):
    """Build a 1-step journal whose state_in/state_out carry the given scopes.

    Builds atoms and journal via real dispatch, then rewraps the entry's
    state_out into an EpistemicSnapshot whose state.scope is the
    requested test scope (allows P-SCOPE-* to test the decorator over
    arbitrary scope shapes).
    """
    atom = make_assertion_atom(
        relation_local="rel",
        subject="subj",
        value="val",
        source_claim_local_ids=("c_x",),
    )
    state_in = make_state(atoms=(), accepted_atom_ids=(), scope=scope_in)
    operator_input = {
        "formula": belief_atom_to_canonical_dict(atom),
        "max_candidates": 8,
        "conflicts": {},
    }
    from propstore.support_revision.snapshot_types import EpistemicStateSnapshot

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
    # Override the resulting state's scope to the requested test scope so
    # the decorator sees that scope when extracting state_out.scope.
    state_out = make_state(
        atoms=next_state.base.atoms,
        accepted_atom_ids=next_state.accepted_atom_ids,
        scope=scope_out,
    )
    operation = TransitionOperation(name="revise", input_atom_id=atom.atom_id)
    entry = make_journal_entry(
        state_in=state_in,
        operation=operation,
        operator=JournalOperator.REVISE,
        operator_input=operator_input,
        state_out=state_out,
    )
    journal = TransitionJournal(entries=(entry,))
    space = synthetic_belief_space_with(atom)
    return space, journal


def test_p_scope_degrade_warns_and_forces_rebind_false() -> None:
    """rebind=True with empty bindings ⇒ warns and degrades to flat view."""
    incomplete = RevisionScope(bindings={}, context_id=None)  # no bindings
    complete = RevisionScope(bindings={}, context_id=None)
    space, journal = _build_journal_with_scope(
        scope_in=complete, scope_out=incomplete
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        view = at_journal_step(space, journal, 0, rebind=True)
    matched = [w for w in caught if "degrading" in str(w.message)]
    assert matched, f"expected a 'degrading' UserWarning, got {[str(w.message) for w in caught]}"
    # Degraded path returns a ClaimView whose bound is None (rebind=False shape)
    assert view.bound is None


def test_p_scope_require_raises_on_missing_commit_for_heavy() -> None:
    """heavy=True without scope.commit ⇒ ValueError, no fallback."""
    incomplete = RevisionScope(
        bindings={"k": "v"}, context_id=None, branch=None, commit=None
    )
    space, journal = _build_journal_with_scope(
        scope_in=incomplete, scope_out=incomplete
    )
    with pytest.raises(ValueError, match=r"commit"):
        at_journal_step(space, journal, 0, heavy=True)


def test_p_scope_noop_rebind_returns_observable_bound_view() -> None:
    """When scope is complete and rebind=True, view.bound is observably set.

    Round-1's sin: rebind=True silently degraded to rebind=False but the
    test only asserted "view is not None". Here we assert the rebind path
    *actually* produced an observable bound artifact different in shape
    from the rebind=False path.
    """
    complete = RevisionScope(
        bindings={"k": "v"},
        context_id=None,
        branch="main",
        commit="0" * 40,
    )
    space, journal = _build_journal_with_scope(
        scope_in=complete, scope_out=complete
    )
    flat = at_journal_step(space, journal, 0, rebind=False)
    rebound = at_journal_step(space, journal, 0, rebind=True)
    # The rebind path MUST produce a different observable shape.
    assert flat.bound is None
    assert rebound.bound is not None
    # And the bound view must carry the scope's bindings — proof the
    # rebind actually rebound.
    assert dict(rebound.bound.bindings) == {"k": "v"}
    # And the restricted_to set must equal the projected claim_ids.
    assert rebound.bound.restricted_to == frozenset(rebound.claim_ids())
