"""Source/store harvesting helpers for the ASPIC bridge."""

from __future__ import annotations

from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import AuthoredJustificationStore, StanceStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.justifications import (
    CanonicalJustification,
    claim_justifications_from_active_graph,
)
from propstore.core.relation_types import ATTACK_TYPES, SUPPORT_TYPES
from propstore.core.row_types import StanceRow, coerce_stance_row


def _extract_stance_rows(
    store: StanceStore,
    active_by_id: dict[str, ActiveClaim],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[StanceRow]:
    """Extract stance rows from either the active graph or the stance store."""

    if active_graph is not None:
        active_ids = set(active_graph.active_claim_ids)
        rows: list[StanceRow] = []
        for relation in active_graph.compiled.relations:
            if relation.source_id not in active_ids or relation.target_id not in active_ids:
                continue
            if (
                relation.relation_type not in ATTACK_TYPES
                and relation.relation_type not in SUPPORT_TYPES
            ):
                continue
            rows.append(
                StanceRow.from_mapping(
                    {
                        "claim_id": relation.source_id,
                        "target_claim_id": relation.target_id,
                        "stance_type": relation.relation_type,
                        **dict(relation.attributes),
                    }
                )
            )
        return rows

    return [
        coerce_stance_row(row)
        for row in store.stances_between(set(active_by_id))
    ]


def _extract_justifications(
    store: StanceStore,
    active_by_id: dict[str, ActiveClaim],
    stance_rows: list[StanceRow],
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
        reported = [
            CanonicalJustification(
                justification_id=f"reported:{claim_id}",
                conclusion_claim_id=claim_id,
                rule_kind="reported_claim",
            )
            for claim_id in sorted(active_by_id)
        ]
        return sorted(reported + authored)

    if active_graph is not None:
        return list(claim_justifications_from_active_graph(active_graph))

    justifications: list[CanonicalJustification] = [
        CanonicalJustification(
            justification_id=f"reported:{claim_id}",
            conclusion_claim_id=claim_id,
            rule_kind="reported_claim",
        )
        for claim_id in sorted(active_by_id)
    ]
    for row in stance_rows:
        if row.stance_type not in {"supports", "explains"}:
            continue
        justifications.append(
            CanonicalJustification(
                justification_id=f"{row.stance_type}:{row.claim_id}->{row.target_claim_id}",
                conclusion_claim_id=row.target_claim_id,
                premise_claim_ids=(row.claim_id,),
                rule_kind=row.stance_type,
                attributes=tuple(row.attributes.items()),
            )
        )
    return sorted(justifications)
