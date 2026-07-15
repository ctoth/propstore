"""WorldQuery <-> EpistemicSnapshot bridge — minimal projection surface.

Per quire/plans/worldline-journal-bridge-2026-05-02.md sections 4 + 11.

The bridge exposes ``at_journal_step(belief_space, journal, k, *, heavy)``
returning a :class:`~propstore.world.types.ClaimView`. The function is
parameterized over a :class:`BeliefSpaceQuery` Protocol — both
:class:`~propstore.world.model.WorldQuery` and the synthetic test belief space
satisfy it. This means the property suite can run against an in-memory belief
space without spinning up a real sidecar per case, while
``WorldQuery.at_journal_step`` remains the public production surface.

Correctness, not faking: ``at_journal_step`` reads
``journal.entries[k].state_out`` and projects it through
:func:`~propstore.support_revision.projection.snapshot_to_claim_ids`. The
Dixon-equivalence property (P5) is *independently* verified against an oracle
that re-runs ``support_revision.dispatch.dispatch`` step-by-step — see
``tests/fixtures/journal.direct_dispatch``.

Substrate boundary (CLAUDE.md): the belief space returns charter
:class:`~propstore.families.claims.Claim` rows directly — there is no
``ClaimRow`` second spelling and no coercer at the boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.support_revision.scope_policy import scope_policy
from propstore.world.types import ClaimView

if TYPE_CHECKING:
    from propstore.families.claims import Claim
    from propstore.support_revision.history import TransitionJournal


@runtime_checkable
class BeliefSpaceQuery(Protocol):
    """Surface a belief space must expose for the bridge.

    :class:`~propstore.world.model.WorldQuery` and the synthetic test fixture
    both implement ``claims_by_ids``.
    """

    def claims_by_ids(self, claim_ids: set[str]) -> Mapping[str, Claim]: ...


@scope_policy(
    extract_from="journal",
    extract_step="k",
    require={"heavy": ("commit",)},
)
def at_journal_step(
    belief_space: BeliefSpaceQuery,
    journal: TransitionJournal,
    k: int,
    *,
    heavy: bool = False,
) -> ClaimView:
    """Project the claims accepted at step ``k`` of the journal.

    Per Bonanno [2007, 2010]: the journal is a branching-time history; state_out
    at step k is the belief state along that history. Per Dixon [1993]: this
    projection is behaviourally equivalent to running the journal's operations
    against the live store, modulo the lossy projection at the AGM boundary
    (projection.py:40-58).

    Parameters
    ----------
    belief_space:
        Object exposing ``claims_by_ids``. ``WorldQuery`` satisfies this.
    journal:
        The captured ``TransitionJournal``.
    k:
        Step index, 0-based.
    heavy:
        If ``True``, dispatch to :mod:`propstore.world.journal_replay` for
        re-derived stances and conflicts. Requires ``scope.commit``.

    Raises
    ------
    IndexError
        If ``k`` is out of range for the journal's entries.
    """
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
    return ClaimView(claims=rows, scope=scope)
