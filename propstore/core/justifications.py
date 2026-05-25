"""Canonical justification records for structured argument construction."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from quire.charters import FamilyModel

if TYPE_CHECKING:
    from propstore.core.graph_types import WorldActivationGraph, ProvenanceRecord


class Justification(FamilyModel):
    @property
    def premise_ids(self) -> tuple[str, ...]:
        loaded = json.loads(self.premise_claim_ids)
        if not isinstance(loaded, list):
            raise ValueError("justification premise_claim_ids must decode to a list")
        return tuple(str(item) for item in loaded)

    def provenance_record(self) -> ProvenanceRecord | None:
        if self.provenance_json is None or self.provenance_json == "":
            return None
        loaded = json.loads(self.provenance_json)
        if not isinstance(loaded, Mapping):
            raise ValueError("justification provenance_json must decode to a mapping")
        from propstore.core.graph_types import ProvenanceRecord

        return ProvenanceRecord.from_json_payload(loaded)

    def to_canonical(self) -> CanonicalJustification:
        attributes = tuple(
            (key, getattr(self, key))
            for key in ("source_relation_type", "source_claim_id")
            if getattr(self, key) is not None
        )
        return CanonicalJustification.from_components(
            justification_id=str(self.id),
            conclusion_claim_id=str(self.conclusion_claim_id),
            premise_claim_ids=self.premise_ids,
            rule_kind=str(self.justification_kind),
            rule_strength=str(self.rule_strength or "defeasible"),
            provenance=self.provenance_record(),
            attributes=attributes,
        )


@dataclass(frozen=True, order=True)
class CanonicalJustification:
    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    rule_strength: str = "defeasible"
    provenance: ProvenanceRecord | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "premise_claim_ids", tuple(str(item) for item in self.premise_claim_ids))
        object.__setattr__(self, "attributes", tuple(self.attributes))

    @classmethod
    def from_components(
        cls,
        *,
        justification_id: str,
        conclusion_claim_id: str,
        premise_claim_ids: Iterable[str] = (),
        rule_kind: str = "reported_claim",
        rule_strength: str = "defeasible",
        provenance: ProvenanceRecord | None = None,
        attributes: Iterable[tuple[str, Any]] = (),
    ) -> CanonicalJustification:
        return cls(
            justification_id=str(justification_id),
            conclusion_claim_id=str(conclusion_claim_id),
            premise_claim_ids=tuple(str(item) for item in premise_claim_ids),
            rule_kind=str(rule_kind),
            rule_strength=str(rule_strength),
            provenance=provenance,
            attributes=tuple(attributes),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "justification_id": self.justification_id,
            "conclusion_claim_id": self.conclusion_claim_id,
            "premise_claim_ids": list(self.premise_claim_ids),
            "rule_kind": self.rule_kind,
            "rule_strength": self.rule_strength,
        }
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalJustification:
        from propstore.core.graph_types import ProvenanceRecord

        provenance_data = data.get("provenance")
        raw_attributes = data.get("attributes")
        attributes = (
            tuple(sorted((str(key), item) for key, item in raw_attributes.items()))
            if isinstance(raw_attributes, Mapping)
            else ()
        )
        return cls.from_components(
            justification_id=str(data["justification_id"]),
            conclusion_claim_id=str(data["conclusion_claim_id"]),
            premise_claim_ids=tuple(str(item) for item in data.get("premise_claim_ids") or ()),
            rule_kind=str(data.get("rule_kind") or "reported_claim"),
            rule_strength=str(data.get("rule_strength") or "defeasible"),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_json_payload(provenance_data)
            ),
            attributes=attributes,
        )


def claim_justifications_from_active_graph(
    active_graph: WorldActivationGraph,
) -> tuple[CanonicalJustification, ...]:
    active_ids = set(active_graph.active_claim_ids)
    claim_nodes = {
        claim.claim_id: claim
        for claim in active_graph.compiled.claims
        if claim.claim_id in active_ids
    }

    justifications: list[CanonicalJustification] = [
        CanonicalJustification.from_components(
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
            CanonicalJustification.from_components(
                justification_id=(
                    f"{relation.relation_type}:{relation.source_id}->{relation.target_id}"
                ),
                conclusion_claim_id=relation.target_id,
                premise_claim_ids=(relation.source_id,),
                rule_kind=relation.relation_type,
                provenance=relation.provenance,
                attributes=relation.attributes,
            )
        )

    return tuple(sorted(justifications))
