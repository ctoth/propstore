"""Journal-step projection over a belief-space query surface.

``at_journal_step(belief_space, journal, k, *, rebind, heavy)`` projects the
claim rows accepted by ``journal.entries[k].state_out``. ``WorldQuery`` uses
the same function as the property tests, so production and synthetic belief
spaces share the journal projection semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from propstore.families.claims.declaration import Claim
from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.support_revision.scope_policy import scope_policy
from propstore.world.types import ClaimView


@runtime_checkable
class BeliefSpaceQuery(Protocol):
    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, Claim]: ...

    def bind_for_view(
        self,
        *,
        bindings: Mapping[str, object],
        context_id: str | None,
        restricted_to: frozenset[str],
    ) -> object: ...


@scope_policy(
    extract_from="journal",
    extract_step="k",
    degrade={"rebind": ("bindings",)},
    require={"heavy": ("commit",)},
)
def at_journal_step(
    belief_space: BeliefSpaceQuery,
    journal: TransitionJournal,
    k: int,
    *,
    rebind: bool = False,
    heavy: bool = False,
) -> ClaimView:
    """Project the claims accepted at step ``k`` of the journal."""
    if not 0 <= k < len(journal.entries):
        raise IndexError(
            f"step {k} out of range for {len(journal.entries)}-step journal"
        )

    if heavy:
        from propstore.world.journal_replay import replay_at_step

        return replay_at_step(belief_space, journal, k)

    snap = journal.entries[k].state_out
    claim_ids = snapshot_to_claim_ids(snap)
    rows = belief_space.claims_by_ids(claim_ids)
    scope = snap.state.scope
    bound = None
    if rebind:
        bound = belief_space.bind_for_view(
            bindings=scope.bindings,
            context_id=scope.context_id,
            restricted_to=frozenset(claim_ids),
        )
    return ClaimView(claims=rows, scope=scope, bound=bound)
