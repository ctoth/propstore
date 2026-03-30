"""Canonical runtime graph dataclasses for the semantic core."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.environment import Environment
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    to_claim_id,
    to_claim_ids,
    to_concept_id,
    to_concept_ids,
)
from propstore.core.labels import EnvironmentKey, Label


def _mapping_items(value: Any) -> list[tuple[Any, Any]]:
    return list(value.items())


def _sequence_items(value: Any) -> list[Any]:
    return list(value)


def _pairs_from_mapping(value: Mapping[str, object]) -> list[tuple[str, object]]:
    pairs: list[tuple[str, object]] = []
    for key, item in value.items():
        pairs.append((str(key), item))
    return pairs


def _pairs_from_iterable(value: tuple[tuple[str, object], ...]) -> list[tuple[str, object]]:
    pairs: list[tuple[str, object]] = []
    for key, item in value:
        pairs.append((str(key), item))
    return pairs


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        frozen_items: list[tuple[str, object]] = []
        for key, item in _mapping_items(value):
            frozen_items.append((str(key), _freeze_value(item)))
        return tuple(sorted(frozen_items))
    if isinstance(value, (list, tuple)):
        sequence = _sequence_items(value)
        return tuple(_freeze_value(item) for item in sequence)
    return value


def _normalize_pairs(
    value: Mapping[str, object] | tuple[tuple[str, object], ...] | None,
) -> tuple[tuple[str, object], ...]:
    if value is None:
        return ()
    pairs = _pairs_from_mapping(value) if isinstance(value, Mapping) else _pairs_from_iterable(value)
    return tuple(
        sorted((key, _freeze_value(item)) for key, item in pairs)
    )


def label_to_dict(label: Label | None) -> list[list[str]] | None:
    if label is None:
        return None
    return [list(environment.assumption_ids) for environment in label.environments]


def label_from_dict(data: list[list[str]] | None) -> Label | None:
    if data is None:
        return None
    return Label(tuple(EnvironmentKey(tuple(environment)) for environment in data))


@dataclass(frozen=True, order=True)
class ConceptNode:
    concept_id: ConceptId
    canonical_name: str
    status: str | None = None
    form: str | None = None
    kind_type: str | None = None
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "concept_id": self.concept_id,
            "canonical_name": self.canonical_name,
        }
        if self.status is not None:
            data["status"] = self.status
        if self.form is not None:
            data["form"] = self.form
        if self.kind_type is not None:
            data["kind_type"] = self.kind_type
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConceptNode:
        return cls(
            concept_id=to_concept_id(data["concept_id"]),
            canonical_name=str(data["canonical_name"]),
            status=(None if data.get("status") is None else str(data["status"])),
            form=(None if data.get("form") is None else str(data["form"])),
            kind_type=(None if data.get("kind_type") is None else str(data["kind_type"])),
            attributes=data.get("attributes") or (),
        )


@dataclass(frozen=True, order=True)
class ProvenanceRecord:
    source_table: str | None = None
    source_id: str | None = None
    paper: str | None = None
    page: int | None = None
    extras: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "extras", _normalize_pairs(self.extras))
        if self.page is not None:
            object.__setattr__(self, "page", int(self.page))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> ProvenanceRecord:
        if not data:
            return cls()
        known = {"source_table", "source_id", "paper", "page"}
        extras = {
            str(key): value
            for key, value in data.items()
            if key not in known and value is not None
        }
        return cls(
            source_table=(None if data.get("source_table") is None else str(data["source_table"])),
            source_id=(None if data.get("source_id") is None else str(data["source_id"])),
            paper=(None if data.get("paper") is None else str(data["paper"])),
            page=(None if data.get("page") is None else int(data["page"])),
            extras=tuple(extras.items()),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.source_table is not None:
            data["source_table"] = self.source_table
        if self.source_id is not None:
            data["source_id"] = self.source_id
        if self.paper is not None:
            data["paper"] = self.paper
        if self.page is not None:
            data["page"] = self.page
        data.update(dict(self.extras))
        return data


@dataclass(frozen=True, order=True)
class ClaimNode:
    claim_id: ClaimId
    concept_id: ConceptId
    claim_type: str
    scalar_value: float | str | None = None
    provenance: ProvenanceRecord | None = None
    label: Label | None = field(default=None, compare=False)
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "concept_id": self.concept_id,
            "claim_type": self.claim_type,
        }
        if self.scalar_value is not None:
            data["scalar_value"] = self.scalar_value
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.label is not None:
            data["label"] = label_to_dict(self.label)
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ClaimNode:
        provenance_data = data.get("provenance")
        return cls(
            claim_id=to_claim_id(data["claim_id"]),
            concept_id=to_concept_id(data["concept_id"]),
            claim_type=str(data["claim_type"]),
            scalar_value=data.get("scalar_value"),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_mapping(provenance_data)
            ),
            label=label_from_dict(data.get("label")),
            attributes=data.get("attributes") or (),
        )


@dataclass(frozen=True, order=True)
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: str
    provenance: ProvenanceRecord | None = None
    derived_from: tuple[tuple[str, str], ...] = ()
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "derived_from", tuple(sorted(self.derived_from)))
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
        }
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.derived_from:
            data["derived_from"] = [list(edge) for edge in self.derived_from]
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RelationEdge:
        provenance_data = data.get("provenance")
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            relation_type=str(data["relation_type"]),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_mapping(provenance_data)
            ),
            derived_from=tuple(tuple(edge) for edge in data.get("derived_from") or ()),
            attributes=data.get("attributes") or (),
        )


@dataclass(frozen=True, order=True)
class ParameterizationEdge:
    output_concept_id: ConceptId
    input_concept_ids: tuple[ConceptId, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: str | None = None
    conditions: tuple[str, ...] = ()
    provenance: ProvenanceRecord | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_concept_ids", tuple(self.input_concept_ids))
        object.__setattr__(self, "conditions", tuple(self.conditions))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "output_concept_id": self.output_concept_id,
            "input_concept_ids": list(self.input_concept_ids),
        }
        if self.formula is not None:
            data["formula"] = self.formula
        if self.sympy is not None:
            data["sympy"] = self.sympy
        if self.exactness is not None:
            data["exactness"] = self.exactness
        if self.conditions:
            data["conditions"] = list(self.conditions)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ParameterizationEdge:
        provenance_data = data.get("provenance")
        return cls(
            output_concept_id=to_concept_id(data["output_concept_id"]),
            input_concept_ids=to_concept_ids(data.get("input_concept_ids") or ()),
            formula=(None if data.get("formula") is None else str(data["formula"])),
            sympy=(None if data.get("sympy") is None else str(data["sympy"])),
            exactness=(None if data.get("exactness") is None else str(data["exactness"])),
            conditions=tuple(str(item) for item in data.get("conditions") or ()),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_mapping(provenance_data)
            ),
        )


@dataclass(frozen=True, order=True)
class ConflictWitness:
    left_claim_id: ClaimId
    right_claim_id: ClaimId
    kind: str
    details: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        left, right = sorted((self.left_claim_id, self.right_claim_id))
        object.__setattr__(self, "left_claim_id", to_claim_id(left))
        object.__setattr__(self, "right_claim_id", to_claim_id(right))
        object.__setattr__(self, "details", _normalize_pairs(self.details))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "left_claim_id": self.left_claim_id,
            "right_claim_id": self.right_claim_id,
            "kind": self.kind,
        }
        if self.details:
            data["details"] = dict(self.details)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConflictWitness:
        return cls(
            left_claim_id=to_claim_id(data["left_claim_id"]),
            right_claim_id=to_claim_id(data["right_claim_id"]),
            kind=str(data["kind"]),
            details=data.get("details") or (),
        )


@dataclass(frozen=True)
class CompiledWorldGraph:
    concepts: tuple[ConceptNode, ...] = ()
    claims: tuple[ClaimNode, ...] = ()
    relations: tuple[RelationEdge, ...] = ()
    parameterizations: tuple[ParameterizationEdge, ...] = ()
    conflicts: tuple[ConflictWitness, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "concepts", tuple(sorted(self.concepts)))
        object.__setattr__(self, "claims", tuple(sorted(self.claims)))
        object.__setattr__(self, "relations", tuple(sorted(self.relations)))
        object.__setattr__(self, "parameterizations", tuple(sorted(self.parameterizations)))
        object.__setattr__(self, "conflicts", tuple(sorted(self.conflicts)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "concepts": [concept.to_dict() for concept in self.concepts],
            "claims": [claim.to_dict() for claim in self.claims],
            "relations": [relation.to_dict() for relation in self.relations],
            "parameterizations": [edge.to_dict() for edge in self.parameterizations],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CompiledWorldGraph:
        return cls(
            concepts=tuple(ConceptNode.from_dict(item) for item in data.get("concepts") or ()),
            claims=tuple(ClaimNode.from_dict(item) for item in data.get("claims") or ()),
            relations=tuple(RelationEdge.from_dict(item) for item in data.get("relations") or ()),
            parameterizations=tuple(
                ParameterizationEdge.from_dict(item)
                for item in data.get("parameterizations") or ()
            ),
            conflicts=tuple(ConflictWitness.from_dict(item) for item in data.get("conflicts") or ()),
        )


@dataclass(frozen=True)
class GraphDelta:
    add_claims: tuple[ClaimNode, ...] = ()
    remove_claim_ids: tuple[ClaimId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "add_claims", tuple(sorted(self.add_claims)))
        object.__setattr__(
            self,
            "remove_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.remove_claim_ids)))),
        )

    @property
    def is_identity(self) -> bool:
        return not self.add_claims and not self.remove_claim_ids

    def apply(self, graph: CompiledWorldGraph) -> CompiledWorldGraph:
        claims = {
            claim.claim_id: claim
            for claim in graph.claims
            if claim.claim_id not in self.remove_claim_ids
        }
        for claim in self.add_claims:
            claims[claim.claim_id] = claim
        claim_ids = set(claims)
        original_claim_ids = {claim.claim_id for claim in graph.claims}

        def _relation_is_valid(edge: RelationEdge) -> bool:
            source_is_claim = edge.source_id in original_claim_ids or edge.source_id in claim_ids
            target_is_claim = edge.target_id in original_claim_ids or edge.target_id in claim_ids
            if source_is_claim or target_is_claim:
                return edge.source_id in claim_ids and edge.target_id in claim_ids
            return True

        return CompiledWorldGraph(
            concepts=graph.concepts,
            claims=tuple(claims.values()),
            relations=tuple(edge for edge in graph.relations if _relation_is_valid(edge)),
            parameterizations=graph.parameterizations,
            conflicts=tuple(
                conflict
                for conflict in graph.conflicts
                if conflict.left_claim_id in claim_ids and conflict.right_claim_id in claim_ids
            ),
        )

    def then(self, other: GraphDelta) -> GraphDelta:
        return GraphDelta(
            add_claims=tuple(
                claim
                for claim in self.apply(CompiledWorldGraph()).claims
                if claim.claim_id not in other.remove_claim_ids
            ) + other.add_claims,
            remove_claim_ids=tuple(self.remove_claim_ids) + tuple(other.remove_claim_ids),
        )


@dataclass(frozen=True)
class ActiveWorldGraph:
    compiled: CompiledWorldGraph
    environment: Environment = field(default_factory=Environment)
    active_claim_ids: tuple[ClaimId, ...] = ()
    inactive_claim_ids: tuple[ClaimId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "active_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.active_claim_ids)))),
        )
        object.__setattr__(
            self,
            "inactive_claim_ids",
            tuple(sorted(dict.fromkeys(to_claim_ids(self.inactive_claim_ids)))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "compiled": self.compiled.to_dict(),
            "environment": self.environment.to_dict(),
            "active_claim_ids": list(self.active_claim_ids),
            "inactive_claim_ids": list(self.inactive_claim_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActiveWorldGraph:
        return cls(
            compiled=CompiledWorldGraph.from_dict(data.get("compiled") or {}),
            environment=Environment.from_dict(data.get("environment")),
            active_claim_ids=to_claim_ids(data.get("active_claim_ids") or ()),
            inactive_claim_ids=to_claim_ids(data.get("inactive_claim_ids") or ()),
        )
