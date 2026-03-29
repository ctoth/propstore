from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from propstore.revision.state import EpistemicState
from propstore.world.labelled import Label, SupportQuality


@dataclass(frozen=True)
class RevisionArgumentationView:
    store: Any
    active_claim_ids: frozenset[str]
    active_claims: tuple[dict[str, Any], ...]
    support_metadata: Mapping[str, tuple[Label | None, SupportQuality]]


class RevisionArgumentationStore:
    """Read-only store overlay exposing the claims active in a revision state."""

    def __init__(self, backing_store, active_claims: tuple[dict[str, Any], ...]) -> None:
        self._backing_store = backing_store
        self._active_claims = tuple(dict(claim) for claim in active_claims)
        self._claims_by_id = {
            str(claim["id"]): dict(claim)
            for claim in self._active_claims
            if claim.get("id")
        }
        self._active_claim_ids = frozenset(self._claims_by_id)

    def get_claim(self, claim_id: str) -> dict | None:
        claim = self._claims_by_id.get(str(claim_id))
        return dict(claim) if claim is not None else None

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return [dict(claim) for claim in self._active_claims]
        return [
            dict(claim)
            for claim in self._active_claims
            if claim.get("concept_id") == concept_id
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        requested = {str(claim_id) for claim_id in claim_ids}
        return {
            claim_id: dict(claim)
            for claim_id, claim in self._claims_by_id.items()
            if claim_id in requested
        }

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        requested = self._active_claim_ids & {str(claim_id) for claim_id in claim_ids}
        getter = getattr(self._backing_store, "stances_between", None)
        if not callable(getter):
            return []
        return [
            dict(row)
            for row in getter(set(requested))
            if row.get("claim_id") in requested
            and row.get("target_claim_id") in requested
        ]

    def conflicts(self) -> list[dict]:
        getter = getattr(self._backing_store, "conflicts", None)
        if not callable(getter):
            return []
        return [
            dict(row)
            for row in getter()
            if row.get("claim_a_id") in self._active_claim_ids
            and row.get("claim_b_id") in self._active_claim_ids
        ]

    def has_table(self, name: str) -> bool:
        getter = getattr(self._backing_store, "has_table", None)
        if not callable(getter):
            return False
        return bool(getter(name))

    def __getattr__(self, name: str) -> Any:
        if name == "compiled_graph":
            raise AttributeError(name)
        return getattr(self._backing_store, name)


def project_epistemic_state_argumentation_view(
    backing_store,
    state: EpistemicState,
) -> RevisionArgumentationView:
    """Project an epistemic state into the current argumentation input surfaces."""
    accepted_set = set(state.accepted_atom_ids)
    active_claims: list[dict[str, Any]] = []
    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}

    for atom in state.base.atoms:
        if atom.atom_id not in accepted_set or atom.kind != "claim":
            continue
        claim_id = _claim_id(atom)
        if claim_id is None:
            continue
        claim = dict(atom.payload)
        claim["id"] = claim_id
        active_claims.append(claim)
        if atom.label is not None:
            support_metadata[claim_id] = (atom.label, SupportQuality.EXACT)

    active_claims.sort(key=lambda claim: str(claim.get("id") or ""))
    overlay = RevisionArgumentationStore(backing_store, tuple(active_claims))
    return RevisionArgumentationView(
        store=overlay,
        active_claim_ids=frozenset(overlay._claims_by_id),
        active_claims=tuple(active_claims),
        support_metadata=support_metadata,
    )


def _claim_id(atom) -> str | None:
    payload_id = atom.payload.get("id")
    if payload_id:
        return str(payload_id)
    prefix, _, suffix = atom.atom_id.partition(":")
    if prefix == "claim" and suffix:
        return suffix
    return None
