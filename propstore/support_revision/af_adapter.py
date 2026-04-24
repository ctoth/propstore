from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claim
from propstore.core.row_types import (
    ConflictRow,
    ConflictRowInput,
    StanceRow,
    StanceRowInput,
    coerce_conflict_row,
    coerce_stance_row,
)
from propstore.support_revision.state import EpistemicState
from propstore.core.labels import Label, SupportQuality
from propstore.support_revision.state import is_claim_atom


@dataclass(frozen=True)
class RevisionArgumentationView:
    store: Any
    active_claim_ids: frozenset[str]
    active_claims: tuple[ActiveClaim, ...]
    support_metadata: Mapping[str, tuple[Label | None, SupportQuality]]


@runtime_checkable
class _StanceStore(Protocol):
    def stances_between(self, claim_ids: set[str]) -> Sequence[StanceRowInput]: ...


@runtime_checkable
class _ConflictStore(Protocol):
    def conflicts(self) -> Sequence[ConflictRowInput]: ...


@runtime_checkable
class _TableStore(Protocol):
    def has_table(self, name: str) -> bool: ...


class RevisionArgumentationStore:
    """Read-only store overlay exposing the claims active in a revision state."""

    def __init__(self, backing_store: object, active_claims: tuple[ActiveClaimInput, ...]) -> None:
        self._backing_store = backing_store
        self._active_claims = tuple(coerce_active_claim(claim) for claim in active_claims)
        self._claims_by_id = {
            str(claim.claim_id): claim
            for claim in self._active_claims
        }
        self._active_claim_ids = frozenset(self._claims_by_id)

    def get_claim(self, claim_id: str):
        claim = self._claims_by_id.get(str(claim_id))
        return None if claim is None else claim.row

    def claims_for(self, concept_id: str | None):
        if concept_id is None:
            return [claim.row for claim in self._active_claims]
        return [
            claim.row
            for claim in self._active_claims
            if claim.value_concept_id == concept_id
        ]

    def claims_by_ids(self, claim_ids: set[str]):
        requested = {str(claim_id) for claim_id in claim_ids}
        return {
            claim_id: claim.row
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in requested
        }

    def stances_between(self, claim_ids: set[str]) -> list[StanceRow]:
        requested = self._active_claim_ids & {str(claim_id) for claim_id in claim_ids}
        if not isinstance(self._backing_store, _StanceStore):
            return []
        result: list[StanceRow] = []
        for row_input in self._backing_store.stances_between(set(requested)):
            row = coerce_stance_row(row_input)
            if str(row.claim_id) in requested and str(row.target_claim_id) in requested:
                result.append(row)
        return result

    def conflicts(self) -> list[ConflictRow]:
        if not isinstance(self._backing_store, _ConflictStore):
            return []
        result: list[ConflictRow] = []
        for row_input in self._backing_store.conflicts():
            row = coerce_conflict_row(row_input)
            if (
                str(row.claim_a_id) in self._active_claim_ids
                and str(row.claim_b_id) in self._active_claim_ids
            ):
                result.append(row)
        return result

    def has_table(self, name: str) -> bool:
        if not isinstance(self._backing_store, _TableStore):
            return False
        return bool(self._backing_store.has_table(name))

    def __getattr__(self, name: str) -> Any:
        if name == "compiled_graph":
            raise AttributeError(name)
        return getattr(self._backing_store, name)


def project_epistemic_state_argumentation_view(
    backing_store: object,
    state: EpistemicState,
) -> RevisionArgumentationView:
    """Project an epistemic state into the current argumentation input surfaces."""
    accepted_set = set(state.accepted_atom_ids)
    active_claims: list[ActiveClaim] = []
    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}

    for atom in state.base.atoms:
        if atom.atom_id not in accepted_set or not is_claim_atom(atom):
            continue
        claim = atom.claim
        claim_id = str(claim.claim_id)
        active_claims.append(claim)
        if atom.label is not None:
            support_metadata[claim_id] = (atom.label, SupportQuality.EXACT)

    active_claims.sort(key=lambda claim: str(claim.claim_id))
    overlay = RevisionArgumentationStore(backing_store, tuple(active_claims))
    return RevisionArgumentationView(
        store=overlay,
        active_claim_ids=frozenset(overlay._claims_by_id),
        active_claims=tuple(active_claims),
        support_metadata=support_metadata,
    )


def _claim_id(atom) -> str | None:
    if is_claim_atom(atom):
        return atom.claim_id
    prefix, _, suffix = atom.atom_id.partition(":")
    if prefix == "claim" and suffix:
        return suffix
    return None
