"""Canonical justification records for structured argument construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.graph_types import ActiveWorldGraph, ProvenanceRecord


def _normalize_attrs(
    value: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None,
) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        items = value.items()
    else:
        items = value
    return tuple(sorted((str(key), item) for key, item in items))


@dataclass(frozen=True, order=True)
class CanonicalJustification:
    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    provenance: ProvenanceRecord | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "premise_claim_ids", tuple(str(item) for item in self.premise_claim_ids))
        object.__setattr__(self, "attributes", _normalize_attrs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "justification_id": self.justification_id,
            "conclusion_claim_id": self.conclusion_claim_id,
            "premise_claim_ids": list(self.premise_claim_ids),
            "rule_kind": self.rule_kind,
        }
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalJustification:
        provenance_data = data.get("provenance")
        return cls(
            justification_id=str(data["justification_id"]),
            conclusion_claim_id=str(data["conclusion_claim_id"]),
            premise_claim_ids=tuple(str(item) for item in data.get("premise_claim_ids") or ()),
            rule_kind=str(data.get("rule_kind") or "reported_claim"),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_mapping(provenance_data)
            ),
            attributes=data.get("attributes") or (),
        )


def claim_justifications_from_active_graph(
    active_graph: ActiveWorldGraph,
) -> tuple[CanonicalJustification, ...]:
    active_ids = set(active_graph.active_claim_ids)
    claim_nodes = {
        claim.claim_id: claim
        for claim in active_graph.compiled.claims
        if claim.claim_id in active_ids
    }

    justifications: list[CanonicalJustification] = [
        CanonicalJustification(
            justification_id=f"reported:{claim_id}",
            conclusion_claim_id=claim_id,
            rule_kind="reported_claim",
            provenance=claim_nodes[claim_id].provenance,
        )
        for claim_id in sorted(claim_nodes)
    ]

    for relation in active_graph.compiled.relations:
        if relation.source_id not in active_ids or relation.target_id not in active_ids:
            continue
        if relation.relation_type not in {"supports", "explains"}:
            continue
        justifications.append(
            CanonicalJustification(
                justification_id=(
                    f"{relation.relation_type}:{relation.source_id}->{relation.target_id}"
                ),
                conclusion_claim_id=relation.target_id,
                premise_claim_ids=(relation.source_id,),
                rule_kind=relation.relation_type,
                provenance=relation.provenance,
                attributes=dict(relation.attributes),
            )
        )

    return tuple(sorted(justifications))
