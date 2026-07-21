"""Store-based construction of a probabilistic argumentation projection.

``build_praf`` reads a charter-backed store over an active claim set into the
shared analyzer inputs and projects them onto the propstore PrAF (the value layer
over the formal ``ProbabilisticAF`` kernel). The store surface comes from
``core``; this module does not import the world layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.core.environment import WorldStore

if TYPE_CHECKING:
    from propstore.praf.engine import PropstorePrAF


def build_praf(
    store: WorldStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> PropstorePrAF:
    """Build a probabilistic argumentation projection over the active claim graph.

    P_A comes from ``p_arg_from_claim``; missing calibration is kept as an honest
    omission (a vacuous opinion), never dropped. Primitive attacks/supports carry
    opinion-derived existence probabilities; direct defeats are the post-preference
    semantic relation; Cayrol-derived defeats stay world-derived consequences, not
    authoritative probabilistic inputs (Li, Oren & Norman 2011).
    """

    # Imported here, not at module load: ``core.analyzers`` imports the ``praf``
    # package (for the value-layer engine), so a top-level import here would close
    # an analyzers -> praf -> projection -> analyzers cycle.
    from propstore.core.analyzers import (
        build_praf_from_shared_input,
        shared_analyzer_input_from_store,
    )

    shared = shared_analyzer_input_from_store(
        store, active_claim_ids, comparison=comparison
    )
    return build_praf_from_shared_input(shared)


__all__ = ["build_praf"]
