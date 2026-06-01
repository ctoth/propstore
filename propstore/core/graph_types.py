"""Canonical runtime graph dataclasses for the semantic core."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from typing import Any, cast

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.families.claims.types import ClaimType
from propstore.core.conditions.checked import (
    CheckedCondition,
    CheckedConditionSet,
)
from propstore.core.conditions.codec import condition_ir_from_json
from propstore.core.environment import Environment
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.graph_relation_types import (
    GraphRelationType,
    coerce_graph_relation_type,
)
from propstore.core.id_types import (
    AssumptionId,
    ClaimId,
    ConceptId,
)
from propstore.core.labels import EnvironmentKey, Label
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


def _mapping_items(value: Any) -> list[tuple[Any, Any]]:
    return list(value.items())


def _sequence_items(value: Any) -> list[Any]:
    return list(value)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        empty: dict[str, Any] = {}
        return empty
    if not isinstance(value, Mapping):
        raise ValueError(f"active world graph field '{field_name}' must be a mapping")
    return {str(key): item for key, item in _mapping_items(value)}


def _require_claim_type(value: object) -> ClaimType:
    if not isinstance(value, str):
        raise ValueError("active world graph claim node requires claim_type")
    return ClaimType(value)


def _pairs_from_iterable(
    value: tuple[tuple[str, object], ...],
) -> list[tuple[str, object]]:
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
    pairs = (
        [(str(key), item) for key, item in value.items()]
        if isinstance(value, Mapping)
        else _pairs_from_iterable(value)
    )
    return tuple(sorted((key, _freeze_value(item)) for key, item in pairs))


def label_to_dict(label: Label | None) -> list[list[str]] | None:
    if label is None:
        return None
    return [list(environment.assumption_ids) for environment in label.environments]


def label_from_dict(data: list[list[str]] | None) -> Label | None:
    if data is None:
        return None
    return Label(
        tuple(
            EnvironmentKey(tuple(AssumptionId(value) for value in environment))
            for environment in data
        )
    )


def _condition_to_dict(condition: CheckedCondition) -> dict[str, Any]:
    return {
        "source": condition.source,
        "registry_fingerprint": condition.registry_fingerprint,
        "warnings": list(condition.warnings),
        "encoded_ir": condition.encoded_ir,
    }


def _condition_from_dict(data: Mapping[str, Any]) -> CheckedCondition:
    encoded_ir = data.get("encoded_ir")
    if not isinstance(encoded_ir, str) or not encoded_ir:
        raise ValueError("graph condition requires encoded_ir")
    source = data.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("graph condition requires source")
    registry_fingerprint = data.get("registry_fingerprint")
    if not isinstance(registry_fingerprint, str) or not registry_fingerprint:
        raise ValueError("graph condition requires registry_fingerprint")
    raw_warnings = data.get("warnings") or ()
    if not isinstance(raw_warnings, list | tuple):
        raise ValueError("graph condition warnings must be a sequence")
    warnings = tuple(
        str(warning)
        for warning in cast(tuple[object, ...] | list[object], raw_warnings)
    )
    return CheckedCondition(
        source=source,
        ir=condition_ir_from_json(json.loads(encoded_ir)),
        registry_fingerprint=registry_fingerprint,
        warnings=warnings,
        encoded_ir=encoded_ir,
    )


def _condition_set_from_dicts(
    values: object,
) -> CheckedConditionSet | None:
    if not values:
        return None
    if not isinstance(values, list | tuple):
        raise ValueError("graph claim conditions_ir must be a sequence")
    raw_values = cast(tuple[object, ...] | list[object], values)
    conditions_list: list[CheckedCondition] = []
    for item in raw_values:
        if not isinstance(item, Mapping):
            raise ValueError("graph claim conditions_ir entries must be mappings")
        conditions_list.append(_condition_from_dict(cast(Mapping[str, Any], item)))
    conditions = tuple(conditions_list)
    return CheckedConditionSet(
        conditions=conditions,
        registry_fingerprint=conditions[0].registry_fingerprint,
    )


def _provenance_to_dict(provenance: Provenance | None) -> dict[str, Any] | None:
    if provenance is None:
        return None
    return provenance.to_payload()


def _provenance_from_dict(data: object) -> Provenance | None:
    if data is None:
        return None
    if not isinstance(data, Mapping):
        raise ValueError("opinion provenance must be a mapping")
    payload = cast(Mapping[str, object], data)
    status = payload.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("opinion provenance requires status")
    raw_witnesses = payload.get("witnesses") or ()
    if not isinstance(raw_witnesses, list | tuple):
        raise ValueError("opinion provenance witnesses must be a sequence")
    witnesses: list[ProvenanceWitness] = []
    for raw_witness in cast(tuple[object, ...] | list[object], raw_witnesses):
        if not isinstance(raw_witness, Mapping):
            raise ValueError("opinion provenance witness must be a mapping")
        witness = cast(Mapping[str, object], raw_witness)
        witnesses.append(
            ProvenanceWitness(
                asserter=str(witness["asserter"]),
                timestamp=str(witness["timestamp"]),
                source_artifact_code=str(witness["source_artifact_code"]),
                method=str(witness["method"]),
            )
        )
    graph_name = payload.get("graph_name")
    raw_derived_from = payload.get("derived_from") or ()
    raw_operations = payload.get("operations") or ()
    if not isinstance(raw_derived_from, list | tuple):
        raise ValueError("opinion provenance derived_from must be a sequence")
    if not isinstance(raw_operations, list | tuple):
        raise ValueError("opinion provenance operations must be a sequence")
    return Provenance(
        status=ProvenanceStatus(status),
        witnesses=tuple(witnesses),
        graph_name=(None if graph_name is None else str(graph_name)),
        derived_from=tuple(
            str(value)
            for value in cast(tuple[object, ...] | list[object], raw_derived_from)
        ),
        operations=tuple(
            str(value)
            for value in cast(tuple[object, ...] | list[object], raw_operations)
        ),
    )


def _opinion_to_dict(opinion: Opinion | None) -> dict[str, Any] | None:
    if opinion is None:
        return None
    return {
        "b": opinion.b,
        "d": opinion.d,
        "u": opinion.u,
        "a": opinion.a,
        "provenance": _provenance_to_dict(opinion.provenance),
    }


def _opinion_from_dict(data: object) -> Opinion | None:
    if data is None:
        return None
    if isinstance(data, Opinion):
        return data
    if not isinstance(data, Mapping):
        raise ValueError("opinion field must be a mapping")
    decoded = cast(Mapping[str, object], data)
    values: dict[str, float] = {}
    for key in ("b", "d", "u", "a"):
        value = decoded[key]
        if isinstance(value, bool) or not isinstance(value, int | float | str):
            raise ValueError(f"opinion field {key!r} must be numeric")
        values[key] = float(value)
    return Opinion(
        values["b"],
        values["d"],
        values["u"],
        values["a"],
        _provenance_from_dict(decoded.get("provenance")),
        allow_dogmatic=values["u"] <= 1e-9,
    )


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
            concept_id=ConceptId(data["concept_id"]),
            canonical_name=str(data["canonical_name"]),
            status=(None if data.get("status") is None else str(data["status"])),
            form=(None if data.get("form") is None else str(data["form"])),
            kind_type=(
                None if data.get("kind_type") is None else str(data["kind_type"])
            ),
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
    context_id: str | None = None
    source_slug: str | None = None
    source_paper: str | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    opinion: Opinion | None = field(default=None, compare=False)
    confidence: float | None = None
    claim_probability: float | None = None
    effective_sample_size: float | None = None
    source_prior_opinion: Opinion | None = field(default=None, compare=False)
    source_quality_opinion: Opinion | None = field(default=None, compare=False)
    unit: str | None = None
    value_si: float | None = None
    lower_bound_si: float | None = None
    upper_bound_si: float | None = None
    checked_conditions: CheckedConditionSet | None = field(
        default=None,
        compare=False,
    )
    provenance: ProvenanceRecord | None = None
    label: Label | None = field(default=None, compare=False)
    source_assertion_ids: tuple[str, ...] = ()
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_assertion_ids",
            tuple(
                sorted(dict.fromkeys(str(value) for value in self.source_assertion_ids))
            ),
        )
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def attribute_mapping(self) -> dict[str, Any]:
        return dict(self.attributes)

    def attribute_value(self, key: str) -> Any:
        return self.attribute_mapping().get(key)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
        }
        if self.value_concept_id is not None:
            data["value_concept_id"] = self.value_concept_id
        if self.scalar_value is not None:
            data["scalar_value"] = self.scalar_value
        for key in (
            "context_id",
            "source_slug",
            "source_paper",
            "lower_bound",
            "upper_bound",
            "uncertainty",
            "uncertainty_type",
            "sample_size",
            "confidence",
            "claim_probability",
            "effective_sample_size",
            "unit",
            "value_si",
            "lower_bound_si",
            "upper_bound_si",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        if self.checked_conditions is not None and self.checked_conditions.conditions:
            data["conditions_ir"] = [
                _condition_to_dict(condition)
                for condition in self.checked_conditions.conditions
            ]
        for key in ("opinion", "source_prior_opinion", "source_quality_opinion"):
            opinion_data = _opinion_to_dict(getattr(self, key))
            if opinion_data is not None:
                data[key] = opinion_data
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        if self.label is not None:
            data["label"] = label_to_dict(self.label)
        if self.source_assertion_ids:
            data["source_assertion_ids"] = list(self.source_assertion_ids)
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ClaimNode:
        provenance_data = data.get("provenance")
        return cls(
            claim_id=ClaimId(data["claim_id"]),
            value_concept_id=(
                None
                if data.get("value_concept_id") is None
                else ConceptId(data["value_concept_id"])
            ),
            claim_type=_require_claim_type(data["claim_type"]),
            scalar_value=data.get("scalar_value"),
            context_id=(
                None if data.get("context_id") is None else str(data["context_id"])
            ),
            source_slug=(
                None if data.get("source_slug") is None else str(data["source_slug"])
            ),
            source_paper=(
                None if data.get("source_paper") is None else str(data["source_paper"])
            ),
            lower_bound=data.get("lower_bound"),
            upper_bound=data.get("upper_bound"),
            uncertainty=data.get("uncertainty"),
            uncertainty_type=(
                None
                if data.get("uncertainty_type") is None
                else str(data["uncertainty_type"])
            ),
            sample_size=(
                None if data.get("sample_size") is None else int(data["sample_size"])
            ),
            opinion=_opinion_from_dict(data.get("opinion")),
            confidence=data.get("confidence"),
            claim_probability=data.get("claim_probability"),
            effective_sample_size=data.get("effective_sample_size"),
            source_prior_opinion=_opinion_from_dict(data.get("source_prior_opinion")),
            source_quality_opinion=_opinion_from_dict(
                data.get("source_quality_opinion")
            ),
            unit=(None if data.get("unit") is None else str(data["unit"])),
            value_si=data.get("value_si"),
            lower_bound_si=data.get("lower_bound_si"),
            upper_bound_si=data.get("upper_bound_si"),
            checked_conditions=_condition_set_from_dicts(data.get("conditions_ir")),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_json_payload(provenance_data)
            ),
            label=label_from_dict(data.get("label")),
            source_assertion_ids=tuple(
                str(value) for value in data.get("source_assertion_ids") or ()
            ),
            attributes=data.get("attributes") or (),
        )


@dataclass(frozen=True, order=True)
class RelationEdge:
    source_id: str
    target_id: str
    relation_type: GraphRelationType
    opinion: Opinion | None = field(default=None, compare=False)
    provenance: ProvenanceRecord | None = None
    derived_from: tuple[tuple[str, str], ...] = ()
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relation_type",
            coerce_graph_relation_type(self.relation_type),
        )
        object.__setattr__(self, "derived_from", tuple(sorted(self.derived_from)))
        object.__setattr__(self, "attributes", _normalize_pairs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
        }
        opinion_data = _opinion_to_dict(self.opinion)
        if opinion_data is not None:
            data["opinion"] = opinion_data
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
            opinion=_opinion_from_dict(data.get("opinion")),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_json_payload(provenance_data)
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
    exactness: Exactness | None = None
    conditions: tuple[CelExpr, ...] = ()
    checked_conditions: CheckedConditionSet | None = None
    provenance: ProvenanceRecord | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "exactness", coerce_exactness(self.exactness))
        object.__setattr__(self, "input_concept_ids", tuple(self.input_concept_ids))
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
        if self.checked_conditions is not None:
            data["conditions_ir"] = [
                _condition_to_dict(condition)
                for condition in self.checked_conditions.conditions
            ]
        if self.provenance is not None:
            data["provenance"] = self.provenance.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ParameterizationEdge:
        provenance_data = data.get("provenance")
        return cls(
            output_concept_id=ConceptId(data["output_concept_id"]),
            input_concept_ids=tuple(
                ConceptId(value) for value in data.get("input_concept_ids") or ()
            ),
            formula=(None if data.get("formula") is None else str(data["formula"])),
            sympy=(None if data.get("sympy") is None else str(data["sympy"])),
            exactness=coerce_exactness(data.get("exactness")),
            conditions=to_cel_exprs(str(item) for item in data.get("conditions") or ()),
            checked_conditions=_condition_set_from_dicts(data.get("conditions_ir")),
            provenance=(
                None
                if provenance_data is None
                else ProvenanceRecord.from_json_payload(provenance_data)
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
        object.__setattr__(self, "left_claim_id", ClaimId(left))
        object.__setattr__(self, "right_claim_id", ClaimId(right))
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
            left_claim_id=ClaimId(data["left_claim_id"]),
            right_claim_id=ClaimId(data["right_claim_id"]),
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
        object.__setattr__(
            self, "parameterizations", tuple(sorted(self.parameterizations))
        )
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
            concepts=tuple(
                ConceptNode.from_dict(item) for item in data.get("concepts") or ()
            ),
            claims=tuple(
                ClaimNode.from_dict(item) for item in data.get("claims") or ()
            ),
            relations=tuple(
                RelationEdge.from_dict(item) for item in data.get("relations") or ()
            ),
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
            tuple(
                sorted(
                    dict.fromkeys(
                        tuple(ClaimId(value) for value in self.remove_claim_ids)
                    )
                )
            ),
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
            source_is_claim = (
                edge.source_id in original_claim_ids or edge.source_id in claim_ids
            )
            target_is_claim = (
                edge.target_id in original_claim_ids or edge.target_id in claim_ids
            )
            if source_is_claim or target_is_claim:
                return edge.source_id in claim_ids and edge.target_id in claim_ids
            return True

        return CompiledWorldGraph(
            concepts=graph.concepts,
            claims=tuple(claims.values()),
            relations=tuple(
                edge for edge in graph.relations if _relation_is_valid(edge)
            ),
            parameterizations=graph.parameterizations,
            conflicts=tuple(
                conflict
                for conflict in graph.conflicts
                if conflict.left_claim_id in claim_ids
                and conflict.right_claim_id in claim_ids
            ),
        )

    def then(self, other: GraphDelta) -> GraphDelta:
        return GraphDelta(
            add_claims=tuple(
                claim
                for claim in self.apply(CompiledWorldGraph()).claims
                if claim.claim_id not in other.remove_claim_ids
            )
            + other.add_claims,
            remove_claim_ids=tuple(self.remove_claim_ids)
            + tuple(other.remove_claim_ids),
        )


@dataclass(frozen=True)
class WorldActivationGraph:
    compiled: CompiledWorldGraph
    environment: Environment = field(default_factory=Environment)
    active_claim_ids: tuple[ClaimId, ...] = ()
    inactive_claim_ids: tuple[ClaimId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "active_claim_ids",
            tuple(
                sorted(
                    dict.fromkeys(
                        tuple(ClaimId(value) for value in self.active_claim_ids)
                    )
                )
            ),
        )
        object.__setattr__(
            self,
            "inactive_claim_ids",
            tuple(
                sorted(
                    dict.fromkeys(
                        tuple(ClaimId(value) for value in self.inactive_claim_ids)
                    )
                )
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "compiled": self.compiled.to_dict(),
            "environment": self.environment.to_dict(),
            "active_claim_ids": list(self.active_claim_ids),
            "inactive_claim_ids": list(self.inactive_claim_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorldActivationGraph:
        return cls(
            compiled=CompiledWorldGraph.from_dict(
                _optional_mapping(data.get("compiled"), "compiled")
            ),
            environment=Environment.from_dict(data.get("environment")),
            active_claim_ids=tuple(
                ClaimId(value) for value in data.get("active_claim_ids") or ()
            ),
            inactive_claim_ids=tuple(
                ClaimId(value) for value in data.get("inactive_claim_ids") or ()
            ),
        )
