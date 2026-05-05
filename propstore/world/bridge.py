"""WorldQuery <-> EpistemicSnapshot bridge — minimal projection surface.

Per quire/plans/worldline-journal-bridge-2026-05-02.md sections 4 + 11.

The bridge exposes ``at_journal_step(belief_space, journal, k, *, rebind, heavy)``
returning a ``ClaimView``. The function is parameterized over a
``BeliefSpaceQuery`` Protocol — both ``WorldQuery`` and the synthetic
test belief space satisfy it. This means the property suite can run
against an in-memory belief space without spinning up a real sidecar
per case, while ``WorldQuery.at_journal_step`` remains the public
production surface.

Correctness, not faking: ``at_journal_step`` reads
``journal.entries[k].state_out`` and projects it through
``snapshot_to_claim_ids``. The Dixon-equivalence property (P5) is
*independently* verified against an oracle that re-runs
``support_revision.dispatch.dispatch`` step-by-step — see
``tests/fixtures/journal.direct_dispatch``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from propstore.core.row_types import ClaimRow
from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.projection import snapshot_to_claim_ids
from propstore.support_revision.scope_policy import scope_policy
from propstore.world.types import ClaimView


@runtime_checkable
class BeliefSpaceQuery(Protocol):
    """Surface a belief space must expose for the bridge.

    ``WorldQuery`` implements ``claims_by_ids``; the synthetic test
    fixture implements both ``claims_by_ids`` and ``bind_for_view``.
    """

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, ClaimRow]: ...

    def bind_for_view(
        self,
        *,
        bindings: Mapping[str, Any],
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
    """Project the claims accepted at step ``k`` of the journal.

    Per Bonanno [2007, 2010]: the journal is a branching-time history;
    state_out at step k is the belief state along that history. Per
    Dixon [1993]: this projection is behaviourally equivalent to
    running the journal's operations against the live store, modulo
    the lossy projection at the AGM boundary
    (projection.py:46-47, 164-185).

    Parameters
    ----------
    belief_space:
        Object exposing ``claims_by_ids`` (and, for ``rebind=True``,
        ``bind_for_view``). ``WorldQuery`` satisfies this.
    journal:
        The captured ``TransitionJournal``.
    k:
        Step index, 0-based.
    rebind:
        If ``True``, the returned ``ClaimView`` carries an observable
        ``bound`` artifact so callers can re-derive against the
        snapshot's scope. The ``@scope_policy`` decorator (see
        ``propstore.support_revision.scope_policy``) governs degradation
        when scope fields are absent.
    heavy:
        If ``True``, dispatch to ``propstore.world.journal_replay`` for
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
    bound = None
    if rebind:
        # Real binding: bind_for_view returns an observable artifact carrying
        # the bindings/context/restricted_to set so callers can verify the
        # rebind path actually rebound. No silent no-op.
        bound = belief_space.bind_for_view(
            bindings=scope.bindings,
            context_id=scope.context_id,
            restricted_to=frozenset(claim_ids),
        )
    return ClaimView(claims=rows, scope=scope, bound=bound)
