"""Canonical runtime graph dataclasses for the semantic core.

A :class:`CompiledWorldGraph` is the content-addressed snapshot of the corpus the
world layer renders over: concepts, claims, concept/stance relation edges,
parameterization edges, and conflict witnesses, each a frozen, ordered value with
``to_dict``/``from_dict`` round-trips. An :class:`ActiveWorldGraph` pairs a
compiled graph with the :class:`~propstore.core.environment.Environment` it was
activated under and the active/inactive claim partition. A :class:`GraphDelta` is
the hypothetical-edit primitive worldline reasoning applies to a compiled graph.

Conditions are condition-ir's own ``CheckedConditionSet`` serialized with that
package's json codec (``checked_condition_set_to_json``); claim labels are the
core :class:`~propstore.core.labels.Label`. propstore mirrors neither — it stores
the package/core spelling directly (CLAUDE.md substrate discipline).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from condition_ir import (
    CelExpr,
    CheckedConditionSet,
    checked_condition_set_from_json,
    checked_condition_set_to_json,
    to_cel_exprs,
)

from propstore.core.environment import Environment
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.graph_relation_types import (
    GraphRelationType,
    coerce_graph_relation_type,
)
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    to_claim_id,
    to_claim_ids,
    to_concept_id,
    to_concept_ids,
)
from propstore.core.labels import Label, label_from_dict, label_to_dict
from propstore.families.claims import ClaimType


def _coerce_claim_type(value: object) -> ClaimType:
    if isinstance(value, ClaimType):
        return value
    return ClaimType(str(value))


def _require_claim_type(value: object) -> ClaimType:
    if value is None:
        raise ValueError("world graph claim node requires claim_type")
    return _coerce_claim_type(value)


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _is_sequence(value: object) -> TypeGuard[Sequence[Any]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not _is_mapping(value):
        raise ValueError(f"world graph field '{field_name}' must be a mapping")
    return {str(key): item for key, item in value.items()}


def _freeze_value(value: object) -> object:
    if _is_mapping(value):
        return tuple(sorted((str(key), _freeze_value(item)) for key, item in value.items()))
    if _is_sequence(value):
        return tuple(_freeze_value(item) for item in value)
    return value


def _normalize_pairs(
    value: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None,
) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    pairs = list(value.items()) if isinstance(value, Mapping) else list(value)
    return tuple(sorted((str(key), _freeze_value(item)) for key, item in pairs))


def _condition_set_to_json(condition_set: CheckedConditionSet) -> dict[str, Any]:
    return checked_condition_set_to_json(condition_set)


def _condition_set_from_json(value: object) -> CheckedConditionSet | None:
    if not value:
        return None
    if not _is_mapping(value):
        raise ValueError("world graph conditions_ir must decode to a mapping")
    return checked_condition_set_from_json(value)


@dataclass(frozen=True, order=True)
class ConceptNode:
    concept_id: ConceptId
    canonical_name: str
    status: str | None = None
    form: str | None = None
    kind_type: str | None = None
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def attribute_mapping(self) -> dict[str, Any]:
        return dict(self.attributes)

    def attribute_value(self, key: str) -> Any:
        return self.attribute_mapping().get(key)

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
            status=None if data.get("status") is None else str(data["status"]),
            form=None if data.get("form") is None else str(data["form"]),
            kind_type=None if data.get("kind_type") is None else str(data["kind_type"]),
            attributes=_normalize_pairs(data.get("attributes")),
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
            source_table=(
                None if data.get("source_table") is None else str(data["source_table"])
            ),
            source_id=None if data.get("source_id") is None else str(data["source_id"]),
            paper=None if data.get("paper") is None else str(data["paper"]),
            page=None if data.get("page") is None else int(data["page"]),
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
    claim_type: ClaimType
    value_concept_id: ConceptId | None = None
    scalar_value: float | str | None = None
    checked_conditions: CheckedConditionSet | None = field(default=None, compare=False)
    provenance: ProvenanceRecord | None = None
    label: Label | None = field(default=None, compare=False)
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_id", to_claim_id(self.claim_id))
        object.__setattr__(self, "claim_type", _coerce_claim_type(self.claim_type))
        if self.value_concept_id is not None:
            object.__setattr__(self, "value_concept_id", to_concept_id(self.value_concept_id))
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def attribute_mapping(self) -> dict[str, Any]:
        return dict(self.attributes)

    def attribute_value(self, key: str) -> Any:
        return self.attribute_mapping().get(key)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
        }
        if self.value_concept_id is not None:
            data["value_concept_id"] = self.value_concept_id
        if self.scalar_value is not None:
            data["scalar_value"] = self.scalar_value
        if self.checked_conditions is not None and self.checked_conditions.conditions:
            data["conditions_ir"] = _condition_set_to_json(self.checked_conditions)
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
            claim_type=_require_claim_type(data.get("claim_type")),
            value_concept_id=(
                None
                if data.get("value_concept_id") is None
                else to_concept_id(data["value_concept_id"])
            ),
            scalar_value=data.get("scalar_value"),
            checked_conditions=_condition_set_from_json(data.get("conditions_ir")),
            provenance=(
                None if provenance_data is None else ProvenanceRecord.from_mapping(provenance_data)
            ),
            label=label_from_dict(data.get("label")),
            attributes=_normalize_pairs(data.get("attributes")),
        )


@dataclass(frozen=True, order=True)
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: GraphRelationType
    provenance: ProvenanceRecord | None = None
    derived_from: tuple[tuple[str, str], ...] = ()
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_type", coerce_graph_relation_type(self.relation_type))
        object.__setattr__(self, "derived_from", tuple(sorted(self.derived_from)))
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
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
            relation_type=coerce_graph_relation_type(data["relation_type"]),
            provenance=(
                None if provenance_data is None else ProvenanceRecord.from_mapping(provenance_data)
            ),
            derived_from=tuple(
                (str(edge[0]), str(edge[1])) for edge in data.get("derived_from") or ()
            ),
            attributes=_normalize_pairs(data.get("attributes")),
        )


@dataclass(frozen=True, order=True)
class ParameterizationEdge:
    output_concept_id: ConceptId
    input_concept_ids: tuple[ConceptId, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    conditions: tuple[CelExpr, ...] = ()
    checked_conditions: CheckedConditionSet | None = field(default=None, compare=False)
    provenance: ProvenanceRecord | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_concept_id", to_concept_id(self.output_concept_id))
        object.__setattr__(self, "input_concept_ids", to_concept_ids(self.input_concept_ids))
        object.__setattr__(self, "exactness", coerce_exactness(self.exactness))
        object.__setattr__(
            self,
            "conditions",
            (
                self.checked_conditions.sources
                if self.checked_conditions is not None
                else to_cel_exprs(self.conditions)
            ),
        )

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
            data["exactness"] = self.exactness.value
        if self.conditions:
            data["conditions"] = list(self.conditions)
        if self.checked_conditions is not None and self.checked_conditions.conditions:
            data["conditions_ir"] = _condition_set_to_json(self.checked_conditions)
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ParameterizationEdge:
        provenance_data = data.get("provenance")
        return cls(
            output_concept_id=to_concept_id(data["output_concept_id"]),
            input_concept_ids=to_concept_ids(data.get("input_concept_ids") or ()),
            formula=None if data.get("formula") is None else str(data["formula"]),
            sympy=None if data.get("sympy") is None else str(data["sympy"]),
            exactness=coerce_exactness(data.get("exactness")),
            conditions=to_cel_exprs(str(item) for item in data.get("conditions") or ()),
            checked_conditions=_condition_set_from_json(data.get("conditions_ir")),
            provenance=(
                None if provenance_data is None else ProvenanceRecord.from_mapping(provenance_data)
            ),
        )


@dataclass(frozen=True, order=True)
class ConflictWitness:
    left_claim_id: ClaimId
    right_claim_id: ClaimId
    kind: str
    details: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        left, right = sorted((str(self.left_claim_id), str(self.right_claim_id)))
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
            details=_normalize_pairs(data.get("details")),
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
            conflicts=tuple(
                ConflictWitness.from_dict(item) for item in data.get("conflicts") or ()
            ),
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
        carried = tuple(
            claim
            for claim in self.apply(CompiledWorldGraph()).claims
            if claim.claim_id not in other.remove_claim_ids
        )
        return GraphDelta(
            add_claims=carried + other.add_claims,
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
            compiled=CompiledWorldGraph.from_dict(_optional_mapping(data.get("compiled"), "compiled")),
            environment=Environment.from_dict(data.get("environment")),
            active_claim_ids=to_claim_ids(data.get("active_claim_ids") or ()),
            inactive_claim_ids=to_claim_ids(data.get("inactive_claim_ids") or ()),
        )
