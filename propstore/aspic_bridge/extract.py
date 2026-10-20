"""Read canonical authored argument inputs for one active claim scope."""

from __future__ import annotations

from propstore.aspic_bridge.translate import StanceInput
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import WorldStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.families.justifications import Justification
from propstore.stances import ATTACK_TYPES, SUPPORT_TYPES


def extract_stance_rows(
    store: WorldStore,
    active_by_id: dict[str, ActiveClaim],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[StanceInput]:
    stances = (
        active_graph.compiled.stances
        if active_graph is not None
        else store.stances_between(set(active_by_id))
    )
    return [
        StanceInput(
            claim_id=stance.source_claim_id,
            target_claim_id=stance.target_claim_id,
            stance_type=stance.stance_type,
        )
        for stance in stances
        if stance.source_claim_id in active_by_id
        and stance.target_claim_id in active_by_id
        and stance.stance_type in ATTACK_TYPES | SUPPORT_TYPES
        and stance.stance_type is not None
    ]


def extract_justifications(
    store: WorldStore,
    active_by_id: dict[str, ActiveClaim],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[Justification]:
    """Keep licences even when a premise is currently inactive.

    Otherwise an unsupported inference conclusion could be mistaken for a fresh
    reported premise. Stance support remains a separate relation capability.
    """
    justifications = (
        active_graph.compiled.justifications
        if active_graph is not None
        else store.all_justifications()
    )
    return sorted(
        (item for item in justifications if item.conclusion in active_by_id),
        key=lambda item: item.justification_id,
    )
