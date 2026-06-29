"""Synthetic fixtures for the worldline-journal-bridge property suite.

These fixtures are real, non-degenerate implementations of the bridge's
input shapes:

- ``direct_dispatch`` calls ``support_revision.dispatch.dispatch`` for every
  step, threading the actual dispatched state forward; it never reads
  ``journal.entries[k].state_out`` and pretends that is the result.
- ``make_assertion_atom`` derives each atom's identity from its situated
  assertion (relation + role bindings + context + condition), as production
  demands, and carries real ``ActiveClaim`` source claims.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.core.active_claims import coerce_active_claim
from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
)
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.history import (
    EpistemicSnapshot,
    JournalOperator,
    TransitionJournal,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.snapshot_types import EpistemicStateSnapshot
from propstore.support_revision.state import (
    AssertionAtom,
    BeliefBase,
    EpistemicState,
    RevisionScope,
)


_DEFAULT_POLICY: Mapping[str, str] = {
    "revision_policy_version": "synthetic-revision-v1",
    "ranking_policy_version": "synthetic-ranking-v1",
    "entrenchment_policy_version": "synthetic-entrenchment-v1",
}


# ---------------------------------------------------------------------------
# minimal real AssertionAtom builder


def make_assertion_atom(
    *,
    relation_local: str,
    subject: str,
    value: str,
    source_claim_local_ids: tuple[str, ...] = (),
) -> AssertionAtom:
    """Return a real ``AssertionAtom`` whose source_claims are real ActiveClaims.

    The atom_id is derived from the assertion (relation + role bindings +
    context + condition), as production demands.
    """
    assertion = SituatedAssertion(
        relation=RelationConceptRef(f"ps:relation:test:{relation_local}"),
        role_bindings=RoleBindingSet(
            (
                RoleBinding("subject", subject),
                RoleBinding("value", value),
            )
        ),
        context=ContextReference("ps:context:test"),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef(
            f"urn:propstore:test-claim-prov:{relation_local}/{subject}/{value}"
        ),
    )
    source_claims = tuple(
        coerce_active_claim({"id": f"propstore:claim:test/{local}"})
        for local in source_claim_local_ids
    )
    return AssertionAtom(
        atom_id=str(assertion.assertion_id),
        assertion=assertion,
        source_claims=source_claims,
    )


# ---------------------------------------------------------------------------
# epistemic state helpers


def make_state(
    *,
    atoms: tuple[AssertionAtom, ...],
    accepted_atom_ids: tuple[str, ...],
    scope: RevisionScope | None = None,
) -> EpistemicState:
    if scope is None:
        scope = RevisionScope(bindings={}, context_id=None)
    base = BeliefBase(scope=scope, atoms=atoms)
    ranking = {atom.atom_id: idx for idx, atom in enumerate(atoms)}
    return EpistemicState(
        scope=scope,
        base=base,
        accepted_atom_ids=accepted_atom_ids,
        ranked_atom_ids=tuple(sorted(ranking, key=lambda a: ranking[a])),
        ranking=ranking,
    )


def make_snapshot(state: EpistemicState) -> EpistemicSnapshot:
    return EpistemicSnapshot.from_state(state)


def empty_snapshot() -> EpistemicSnapshot:
    return make_snapshot(make_state(atoms=(), accepted_atom_ids=()))


# ---------------------------------------------------------------------------
# Journal construction (REAL — uses dispatch to thread state across steps)


def make_journal_entry(
    *,
    state_in: EpistemicState,
    operation: TransitionOperation,
    operator: JournalOperator,
    operator_input: Mapping[str, Any],
    state_out: EpistemicState,
    policy_id: str = "synthetic-policy-v1",
    policy: Mapping[str, str] = _DEFAULT_POLICY,
) -> TransitionJournalEntry:
    return TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=operation,
        policy_id=policy_id,
        operator=operator,
        operator_input=operator_input,
        version_policy_snapshot=policy,
        state_out=state_out,
        explanation={},
    )


def single_chapter_journal(
    *,
    initial_state: EpistemicState,
    revision_atoms: tuple[AssertionAtom, ...],
) -> TransitionJournal:
    """Build a real journal where each entry adds one atom via REVISE.

    The journal is constructed by *running the operators*, not by stuffing
    the expected answer into ``state_out`` and reading it back.
    """
    from propstore.support_revision.snapshot_types import (
        belief_atom_to_canonical_dict,
    )

    state = initial_state
    entries: list[TransitionJournalEntry] = []
    for atom in revision_atoms:
        operator_input: dict[str, Any] = {
            "formula": belief_atom_to_canonical_dict(atom),
            "max_candidates": 8,
            "conflicts": {},
        }
        next_state = dispatch(
            JournalOperator.REVISE,
            state_in=EpistemicStateSnapshot.from_state(state).to_dict(),
            operator_input=operator_input,
            policy=_DEFAULT_POLICY,
        )
        operation = TransitionOperation(
            name="revise",
            input_atom_id=atom.atom_id,
            target_atom_ids=(),
        )
        entries.append(
            make_journal_entry(
                state_in=state,
                operation=operation,
                operator=JournalOperator.REVISE,
                operator_input=operator_input,
                state_out=next_state,
            )
        )
        state = next_state
    return TransitionJournal(entries=tuple(entries))


# ---------------------------------------------------------------------------
# direct_dispatch — the HONEST oracle (calls dispatch.dispatch step-by-step)


def direct_dispatch(journal: TransitionJournal, k: int) -> EpistemicState:
    """Re-execute ``journal.entries[: k+1]`` against ``support_revision.dispatch.dispatch``.

    Threads the *actual dispatch result* of step ``i`` forward as ``state_in``
    for step ``i+1``. Returns the final ``EpistemicState``.

    This is the ground truth for the Dixon-equivalence property. Reading
    ``journal.entries[k].state_out`` is forbidden here.
    """
    if k < 0 or k >= len(journal.entries):
        raise IndexError(
            f"step {k} out of range for {len(journal.entries)}-step journal"
        )
    state_in_payload: Mapping[str, Any] = journal.entries[0].normalized_state_in
    last_state: EpistemicState | None = None
    for index in range(k + 1):
        entry = journal.entries[index]
        last_state = dispatch(
            entry.operator,
            state_in=state_in_payload,
            operator_input=entry.operator_input,
            policy=entry.version_policy_snapshot,
        )
        state_in_payload = EpistemicStateSnapshot.from_state(last_state).to_dict()
    assert last_state is not None
    return last_state
