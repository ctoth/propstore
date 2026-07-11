"""Store/active-graph harvesting helpers for the ASPIC+ bridge.

These read stances and justifications for an active claim scope from either the
active world graph or the charter-backed store, and hand the bridge plain stance
mappings (the :data:`~propstore.aspic_bridge.translate.StanceInput` shape) and
canonical justification records. There is no graph relation mirror for an
authored stance; the active graph carries the ``Stance`` charter directly.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.aspic_bridge.translate import StanceInput
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import AuthoredJustificationStore, StanceStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.justifications import (
    CanonicalJustification,
    claim_justifications_from_active_graph,
)
from propstore.families.relations import Stance
from propstore.stances import ATTACK_TYPES, SUPPORT_TYPES

_STANCE_ROW_RELATION_VALUES = frozenset(
    stance_type.value for stance_type in (ATTACK_TYPES | SUPPORT_TYPES)
)
_SUPPORT_RELATION_VALUES = frozenset(stance_type.value for stance_type in SUPPORT_TYPES)


def _stance_to_input(stance: Stance) -> StanceInput | None:
    if stance.source_claim_id is None or stance.target_claim_id is None:
        return None
    if stance.stance_type is None:
        return None
    return {
        "claim_id": str(stance.source_claim_id),
        "target_claim_id": str(stance.target_claim_id),
        "stance_type": stance.stance_type.value,
    }


def extract_stance_rows(
    store: StanceStore,
    active_by_id: dict[str, ActiveClaim],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[StanceInput]:
    """Extract stance mappings from the active graph or the stance store."""

    if active_graph is not None:
        active_ids = {str(claim_id) for claim_id in active_graph.active_claim_ids}
        rows: list[StanceInput] = []
        for stance in active_graph.compiled.stances:
            if stance.source_claim_id is None or stance.target_claim_id is None:
                continue
            if (
                stance.source_claim_id not in active_ids
                or stance.target_claim_id not in active_ids
            ):
                continue
            if stance.stance_type is None:
                continue
            if stance.stance_type.value not in _STANCE_ROW_RELATION_VALUES:
                continue
            mapped = _stance_to_input(stance)
            if mapped is not None:
                rows.append(mapped)
        return rows

    return [
        mapped
        for stance in store.stances_between(set(active_by_id))
        if (mapped := _stance_to_input(stance)) is not None
    ]


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _stance_field(stance: Mapping[str, Any], key: str) -> str | None:
    value = stance.get(key)
    return None if value is None else str(value)


def extract_justifications(
    store: StanceStore,
    active_by_id: dict[str, ActiveClaim],
    stance_rows: list[StanceInput],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[CanonicalJustification]:
    """Extract canonical justifications for the active claim scope."""

    authored: list[CanonicalJustification] = []
    if isinstance(store, AuthoredJustificationStore):
        authored = [
            justification
            for justification in store.justifications_for_claim_scope(set(active_by_id))
            if justification.rule_kind != "reported_claim"
        ]
    if authored:
        reported = [_reported(claim_id) for claim_id in sorted(active_by_id)]
        return sorted(reported + authored)

    if active_graph is not None:
        return list(claim_justifications_from_active_graph(active_graph))

    justifications: list[CanonicalJustification] = [
        _reported(claim_id) for claim_id in sorted(active_by_id)
    ]
    for row in stance_rows:
        stance_type = _stance_field(row, "stance_type")
        if stance_type not in _SUPPORT_RELATION_VALUES:
            continue
        source_id = _stance_field(row, "claim_id")
        target_id = _stance_field(row, "target_claim_id")
        if source_id is None or target_id is None:
            continue
        justifications.append(
            CanonicalJustification(
                justification_id=f"{stance_type}:{source_id}->{target_id}",
                conclusion_claim_id=target_id,
                premise_claim_ids=(source_id,),
                rule_kind=stance_type,
            )
        )
    return sorted(justifications)


__all__ = ["extract_justifications", "extract_stance_rows"]
