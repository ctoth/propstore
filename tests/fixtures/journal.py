"""Synthetic fixtures for the worldline-journal-bridge property suite.

These fixtures are real, non-degenerate implementations of the bridge's
input shapes. Anti-patterns explicitly avoided (per round-1 NO-MERGE):

- The Mara-Jade fixture is hand-built, not derived from `synthetic_sidecar()`.
- `direct_dispatch` calls `support_revision.dispatch.dispatch` for every
  step, threading the actual dispatched state forward; it never reads
  `journal.entries[k].state_out` and pretends that is the result.
- The synthetic belief space is a real ``BeliefSpaceQuery`` Protocol
  implementation, not a hollow stand-in for ``WorldQuery``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import to_claim_id
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
)
from propstore.core.row_types import ClaimRow
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
# minimal real ClaimRow + AssertionAtom builders


def make_claim_row(claim_local_id: str) -> ClaimRow:
    """Return a real ``ClaimRow`` with deterministic identity for tests."""
    artifact_id = f"propstore:claim:test/{claim_local_id}"
    return ClaimRow(claim_id=to_claim_id(artifact_id), artifact_id=artifact_id)


def make_assertion_atom(
    *,
    relation_local: str,
    subject: str,
    value: str,
    source_claim_local_ids: tuple[str, ...] = (),
) -> AssertionAtom:
    """Return a real ``AssertionAtom`` whose source_claims map to real ClaimRows.

    The atom_id is derived from the assertion (relation + role bindings +
    context + condition), as production demands.
    """
    from propstore.core.active_claims import ActiveClaim

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
        ActiveClaim.from_claim_row(make_claim_row(local))
        for local in source_claim_local_ids
    )
    return AssertionAtom(
        atom_id="",  # __post_init__ overwrites to str(assertion.assertion_id)
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
# Mara-Jade hand-built fixture (HttE-shaped, NOT derived from synthetic_sidecar)


@dataclass(frozen=True)
class MaraJadeFixture:
    """Two atoms (orders, assignment) each carrying a distinct source claim."""

    orders_atom: AssertionAtom
    assignment_atom: AssertionAtom
    state: EpistemicState
    snapshot: EpistemicSnapshot

    @property
    def expected_claim_ids(self) -> frozenset[str]:
        # Asserted by hand from the fixture definition, NOT projected from
        # the journal's accepted_atom_ids.
        return frozenset({
            "propstore:claim:test/mara_learns_orders",
            "propstore:claim:test/mara_assigned_to_find_karrde",
        })


def mara_jade_fixture() -> MaraJadeFixture:
    """Hand-built HttE chapter-1 fixture for the P-MARA gate.

    Two atoms, each carrying exactly one ``source_claim`` whose claim_id
    matches the hand-asserted ``expected_claim_ids`` set.
    """
    orders = make_assertion_atom(
        relation_local="learns_order_from",
        subject="character/mara_jade",
        value="emperor:kill_luke_skywalker",
        source_claim_local_ids=("mara_learns_orders",),
    )
    assignment = make_assertion_atom(
        relation_local="assigned_mission",
        subject="character/mara_jade",
        value="mission:find_talon_karrde",
        source_claim_local_ids=("mara_assigned_to_find_karrde",),
    )
    state = make_state(
        atoms=(orders, assignment),
        accepted_atom_ids=(orders.atom_id, assignment.atom_id),
    )
    return MaraJadeFixture(
        orders_atom=orders,
        assignment_atom=assignment,
        state=state,
        snapshot=make_snapshot(state),
    )


# ---------------------------------------------------------------------------
# Synthetic belief space — a *real* BeliefSpaceQuery, not a fake


@dataclass(frozen=True)
class SyntheticBoundView:
    """Observable artifact of binding under a scope.

    Carries the bound environment so tests can assert ``rebind=True``
    actually produced a different shape than ``rebind=False``.
    """

    bindings: Mapping[str, Any]
    context_id: str | None
    restricted_to: frozenset[str]


@dataclass
class SyntheticBeliefSpace:
    """In-memory belief space satisfying the bridge's surface contract.

    The bridge calls ``claims_by_ids`` and ``bind_for_view`` — both are real
    here. No method silently no-ops; ``bind_for_view`` returns a real
    ``SyntheticBoundView`` with all binding state observable.
    """

    rows: dict[str, ClaimRow] = field(default_factory=dict)

    def add_claim(self, claim_local_id: str) -> ClaimRow:
        row = make_claim_row(claim_local_id)
        self.rows[str(row.claim_id)] = row
        return row

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, ClaimRow]:
        return {cid: self.rows[cid] for cid in claim_ids if cid in self.rows}

    def bind_for_view(
        self,
        *,
        bindings: Mapping[str, Any],
        context_id: str | None,
        restricted_to: frozenset[str],
    ) -> SyntheticBoundView:
        return SyntheticBoundView(
            bindings=dict(bindings),
            context_id=context_id,
            restricted_to=restricted_to,
        )


def synthetic_belief_space_with(*atoms: AssertionAtom) -> SyntheticBeliefSpace:
    """Build a belief space whose rows cover every source_claim of every atom."""
    space = SyntheticBeliefSpace()
    for atom in atoms:
        for claim in atom.source_claims:
            local = _local_from_artifact(str(claim.claim_id))
            space.add_claim(local)
    return space


def _local_from_artifact(claim_id: str) -> str:
    prefix = "propstore:claim:test/"
    if claim_id.startswith(prefix):
        return claim_id[len(prefix):]
    return claim_id


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

    This is the ground truth for the Dixon-equivalence property (P5).
    Reading ``journal.entries[k].state_out`` is the round-1 sin and is
    explicitly forbidden here.
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
