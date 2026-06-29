"""Canonical justification records for structured argument construction.

A :class:`CanonicalJustification` is the propstore-side value describing one
inference licence: a conclusion claim, its premise claims, and the kind/strength
of the rule that links them. The ASPIC+ bridge turns these into ``Rule`` objects
(``reported_claim`` justifications contribute a premise, not a rule). This is the
ONE spelling of a justification record; there is no parallel document mirror.

Non-commitment (CLAUDE.md): this type does not validate ``rule_kind`` /
``rule_strength`` — authoring validation is the source subsystem's job (a later
phase). A justification with an unrecognized kind is still a representable record;
filtering is never a build-time concern here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import msgspec

from propstore.core.graph_relation_types import GraphRelationType
from propstore.provenance import Provenance

if TYPE_CHECKING:
    from propstore.core.graph_types import ActiveWorldGraph

_SUPPORT_RELATION_TYPES = frozenset({GraphRelationType.SUPPORTS, GraphRelationType.EXPLAINS})


def _normalize_attrs(
    value: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None,
) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    items = value.items() if isinstance(value, Mapping) else value
    return tuple(sorted((str(key), item) for key, item in items))


@dataclass(frozen=True, order=True)
class CanonicalJustification:
    """One inference licence: premises, conclusion, and rule kind/strength."""

    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    rule_strength: str = "defeasible"
    provenance: Provenance | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "premise_claim_ids",
            tuple(str(item) for item in self.premise_claim_ids),
        )
        object.__setattr__(self, "attributes", _normalize_attrs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "justification_id": self.justification_id,
            "conclusion_claim_id": self.conclusion_claim_id,
            "premise_claim_ids": list(self.premise_claim_ids),
            "rule_kind": self.rule_kind,
            "rule_strength": self.rule_strength,
        }
        if self.provenance is not None:
            data["provenance"] = msgspec.to_builtins(self.provenance)
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
            rule_strength=str(data.get("rule_strength") or "defeasible"),
            provenance=(
                None
                if provenance_data is None
                else msgspec.convert(provenance_data, Provenance)
            ),
            attributes=tuple(_normalize_attrs(data.get("attributes"))),
        )


def claim_justifications_from_active_graph(
    active_graph: ActiveWorldGraph,
) -> tuple[CanonicalJustification, ...]:
    """Derive canonical justifications from an active world graph.

    Every active claim contributes a ``reported_claim`` justification; every
    active ``supports``/``explains`` relation edge between active claims becomes a
    single-premise justification concluding the edge's target. The result is
    sorted so the projection is deterministic under relation-iteration order
    (CLAUDE.md: the graph never gates; ordering is a render concern). Provenance
    is not carried here — the claim/relation graph carries a
    :class:`~propstore.core.graph_types.ProvenanceRecord`, which is the world
    graph's spelling, not the source-semiring :class:`Provenance` this record
    uses; the two are not interchangeable, so the justification stays
    provenance-free rather than mirror one onto the other.
    """

    active_ids = set(active_graph.active_claim_ids)
    claim_ids = sorted(
        str(claim.claim_id)
        for claim in active_graph.compiled.claims
        if claim.claim_id in active_ids
    )

    justifications: list[CanonicalJustification] = [
        CanonicalJustification(
            justification_id=f"reported:{claim_id}",
            conclusion_claim_id=claim_id,
            rule_kind="reported_claim",
        )
        for claim_id in claim_ids
    ]

    for relation in active_graph.compiled.relations:
        if relation.source_id not in active_ids or relation.target_id not in active_ids:
            continue
        if relation.relation_type not in _SUPPORT_RELATION_TYPES:
            continue
        relation_kind = str(relation.relation_type)
        justifications.append(
            CanonicalJustification(
                justification_id=(
                    f"{relation_kind}:{relation.source_id}->{relation.target_id}"
                ),
                conclusion_claim_id=str(relation.target_id),
                premise_claim_ids=(str(relation.source_id),),
                rule_kind=relation_kind,
                attributes=relation.attributes,
            )
        )

    return tuple(sorted(justifications))


__all__ = ["CanonicalJustification", "claim_justifications_from_active_graph"]
