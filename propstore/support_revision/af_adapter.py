"""Project an epistemic state into the argumentation input surfaces.

The revision package decides which belief atoms are accepted; the argumentation
layer reasons over *claims*. This module bridges the two: it reads an
:class:`~propstore.support_revision.state.EpistemicState`, collects the source
claims of every accepted assertion atom, and exposes them as a read-only overlay
over the backing :class:`~propstore.core.environment.WorldStore` restricted to the
accepted claim set. The overlay returns the ONE canonical charter types
(``Claim`` / ``Stance`` / ``ConflictRecord``) the argumentation builders already
consume — there is no ``*Row`` second spelling (CLAUDE.md substrate boundary).

This module never imports ``belief_set`` or the IC-merge surface: it operates on a
realized ``EpistemicState`` after the formal decision has been made.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claim
from propstore.core.environment import (
    ClaimCatalogStore,
    ClaimLookupStore,
    ConflictStore,
    StanceStore,
)
from propstore.core.labels import Label, SupportQuality
from propstore.support_revision.state import (
    EpistemicState,
    is_assertion_atom,
    is_assumption_atom,
)

if TYPE_CHECKING:
    from propstore.conflict_detector.models import ConflictRecord
    from propstore.families.claims import Claim
    from propstore.families.relations import Stance


@dataclass(frozen=True)
class RevisionArgumentationView:
    """The accepted-claim surface a revision state exposes to argumentation."""

    store: RevisionArgumentationStore
    active_claim_ids: frozenset[str]
    active_claims: tuple[ActiveClaim, ...]
    support_metadata: Mapping[str, tuple[Label | None, SupportQuality]]
    unmapped_atom_ids: tuple[str, ...] = ()
    accepted_assumption_atom_ids: tuple[str, ...] = ()
    revision_event_hashes: tuple[str, ...] = ()


class RevisionArgumentationStore:
    """Read-only store overlay exposing the claims active in a revision state.

    Claim/stance/conflict reads delegate to the backing ``WorldStore`` but are
    restricted to the accepted claim id set; every other attribute access falls
    through to the backing store so the overlay can stand in wherever a
    ``WorldStore`` is expected.
    """

    def __init__(
        self,
        backing_store: object,
        active_claims: tuple[ActiveClaimInput, ...],
    ) -> None:
        self._backing_store = backing_store
        self._active_claims = tuple(coerce_active_claim(claim) for claim in active_claims)
        self._claims_by_id = {str(claim.claim_id): claim for claim in self._active_claims}
        self._active_claim_ids = frozenset(self._claims_by_id)

    def get_claim(self, claim_id: str) -> Claim | None:
        if str(claim_id) not in self._active_claim_ids:
            return None
        if isinstance(self._backing_store, ClaimLookupStore):
            return self._backing_store.get_claim(str(claim_id))
        return None

    def claims_for(self, concept_id: str | None) -> list[Claim]:
        if not isinstance(self._backing_store, ClaimCatalogStore):
            return []
        return [
            claim
            for claim in self._backing_store.claims_for(concept_id)
            if str(claim.claim_id) in self._active_claim_ids
        ]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]:
        requested = self._active_claim_ids & {str(claim_id) for claim_id in claim_ids}
        result: dict[str, Claim] = {}
        for claim_id in requested:
            claim = self.get_claim(claim_id)
            if claim is not None:
                result[claim_id] = claim
        return result

    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        requested = self._active_claim_ids & {str(claim_id) for claim_id in claim_ids}
        if not isinstance(self._backing_store, StanceStore):
            return []
        return [
            stance
            for stance in self._backing_store.stances_between(set(requested))
            if str(stance.source_claim_id) in requested
            and str(stance.target_claim_id) in requested
        ]

    def conflicts(self) -> list[ConflictRecord]:
        if not isinstance(self._backing_store, ConflictStore):
            return []
        return [
            conflict
            for conflict in self._backing_store.conflicts()
            if str(conflict.claim_a_id) in self._active_claim_ids
            and str(conflict.claim_b_id) in self._active_claim_ids
        ]

    def __getattr__(self, name: str) -> Any:
        # Delegate every non-restricted attribute to the backing store so the
        # overlay can substitute for a full ``WorldStore``. ``compiled_graph`` is
        # withheld: the overlay restricts claims, so a cached full graph would be
        # stale.
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
    unmapped_atom_ids: list[str] = []
    accepted_assumption_atom_ids: list[str] = []

    for atom in state.base.atoms:
        if atom.atom_id not in accepted_set:
            continue
        if is_assumption_atom(atom):
            accepted_assumption_atom_ids.append(atom.atom_id)
            continue
        if not is_assertion_atom(atom):
            continue
        if not atom.source_claims:
            unmapped_atom_ids.append(atom.atom_id)
        for claim in atom.source_claims:
            claim_id = str(claim.claim_id)
            active_claims.append(claim)
            if atom.label is not None:
                support_metadata[claim_id] = (atom.label, SupportQuality.EXACT)

    for atom_id, support_sets in state.base.support_sets.items():
        if atom_id not in accepted_set:
            continue
        for support_set in support_sets:
            accepted_assumption_atom_ids.extend(
                str(assumption_id) for assumption_id in support_set
            )

    active_claims.sort(key=lambda claim: str(claim.claim_id))
    overlay = RevisionArgumentationStore(backing_store, tuple(active_claims))
    return RevisionArgumentationView(
        store=overlay,
        active_claim_ids=frozenset(str(claim.claim_id) for claim in active_claims),
        active_claims=tuple(active_claims),
        support_metadata=support_metadata,
        unmapped_atom_ids=tuple(sorted(unmapped_atom_ids)),
        accepted_assumption_atom_ids=tuple(sorted(dict.fromkeys(accepted_assumption_atom_ids))),
        revision_event_hashes=_revision_event_hashes(state),
    )


def _revision_event_hashes(state: EpistemicState) -> tuple[str, ...]:
    event_hashes: list[str] = []
    for episode in state.history:
        if episode.event is None:
            continue
        event_hashes.append(episode.event.content_hash)
    return tuple(event_hashes)
