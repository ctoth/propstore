"""Typed storage-row boundaries for stable sidecar shapes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.conflict_detector.models import ConflictClass, coerce_conflict_class
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.concept_relationship_types import (
    ConceptRelationshipType,
    coerce_concept_relationship_type,
)
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.claim_values import (
    ClaimProvenance,
    ClaimSource,
    SourceOrigin,
    SourceTrust,
)
from propstore.stances import StanceType, coerce_stance_type
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    ContextId,
    JustificationId,
    LogicalId,
    to_claim_id,
    to_concept_id,
    to_context_id,
    to_justification_id,
)


@dataclass(frozen=True)
class ConceptRow:
    concept_id: ConceptId
    canonical_name: str
    status: str | None = None
    definition: str | None = None
    kind_type: str | None = None
    form: str | None = None
    domain: str | None = None
    form_parameters: str | None = None
    primary_logical_id: str | None = None
    logical_ids_json: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ConceptRow:
        known = {
            "id",
            "canonical_name",
            "status",
            "definition",
            "kind_type",
            "form",
            "domain",
            "form_parameters",
            "primary_logical_id",
            "logical_ids_json",
        }
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        return cls(
            concept_id=to_concept_id(row_map["id"]),
            canonical_name=str(row_map["canonical_name"]),
            status=None if row_map.get("status") is None else str(row_map["status"]),
            definition=None if row_map.get("definition") is None else str(row_map["definition"]),
            kind_type=None if row_map.get("kind_type") is None else str(row_map["kind_type"]),
            form=None if row_map.get("form") is None else str(row_map["form"]),
            domain=None if row_map.get("domain") is None else str(row_map["domain"]),
            form_parameters=(
                None
                if row_map.get("form_parameters") is None
                else str(row_map["form_parameters"])
            ),
            primary_logical_id=(
                None
                if row_map.get("primary_logical_id") is None
                else str(row_map["primary_logical_id"])
            ),
            logical_ids_json=(
                None
                if row_map.get("logical_ids_json") is None
                else str(row_map["logical_ids_json"])
            ),
            attributes=attributes,
        )

    def parsed_logical_ids(self) -> list[dict[str, Any]]:
        if not self.logical_ids_json:
            return []
        try:
            loaded = json.loads(self.logical_ids_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.concept_id,
            "canonical_name": self.canonical_name,
        }
        if self.status is not None:
            data["status"] = self.status
        if self.definition is not None:
            data["definition"] = self.definition
        if self.kind_type is not None:
            data["kind_type"] = self.kind_type
        if self.form is not None:
            data["form"] = self.form
        if self.domain is not None:
            data["domain"] = self.domain
        if self.form_parameters is not None:
            data["form_parameters"] = self.form_parameters
        if self.primary_logical_id is not None:
            data["primary_logical_id"] = self.primary_logical_id
            data["logical_id"] = self.primary_logical_id
        if self.logical_ids_json is not None:
            data["logical_ids_json"] = self.logical_ids_json
        data["logical_ids"] = self.parsed_logical_ids()
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class RelationshipRow:
    source_id: str
    target_id: str
    relation_type: ConceptRelationshipType
    conditions_cel: str | None = None
    note: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relation_type",
            coerce_concept_relationship_type(self.relation_type),
        )
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> RelationshipRow:
        known = {"source_id", "target_id", "type", "relation_type", "conditions_cel", "note"}
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        relation_type = row_map.get("relation_type", row_map.get("type"))
        if relation_type is None:
            raise KeyError("relation_type")
        return cls(
            source_id=str(row_map["source_id"]),
            target_id=str(row_map["target_id"]),
            relation_type=coerce_concept_relationship_type(relation_type),
            conditions_cel=(
                None if row_map.get("conditions_cel") is None else str(row_map["conditions_cel"])
            ),
            note=None if row_map.get("note") is None else str(row_map["note"]),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.relation_type.value,
        }
        if self.conditions_cel is not None:
            data["conditions_cel"] = self.conditions_cel
        if self.note is not None:
            data["note"] = self.note
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class ClaimRow:
    claim_id: ClaimId
    artifact_id: str
    claim_type: ClaimType | None = None
    concept_id: ConceptId | None = None
    target_concept: ConceptId | None = None
    logical_ids: tuple[LogicalId, ...] = field(default_factory=tuple)
    version_id: str | None = None
    seq: int | None = None
    value: Any = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    unit: str | None = None
    conditions_cel: str | None = None
    statement: str | None = None
    expression: str | None = None
    sympy_generated: str | None = None
    sympy_error: str | None = None
    name: str | None = None
    measure: str | None = None
    listener_population: str | None = None
    methodology: str | None = None
    notes: str | None = None
    description: str | None = None
    auto_summary: str | None = None
    body: str | None = None
    canonical_ast: str | None = None
    variables_json: str | None = None
    stage: str | None = None
    source: ClaimSource | None = None
    provenance: ClaimProvenance | None = None
    value_si: float | None = None
    lower_bound_si: float | None = None
    upper_bound_si: float | None = None
    context_id: ContextId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))
        if self.claim_type is not None:
            object.__setattr__(self, "claim_type", coerce_claim_type(self.claim_type))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ClaimRow:
        known = {
            "id",
            "artifact_id",
            "type",
            "claim_type",
            "concept_id",
            "target_concept",
            "primary_logical_id",
            "logical_id",
            "logical_ids",
            "logical_ids_json",
            "version_id",
            "seq",
            "value",
            "lower_bound",
            "upper_bound",
            "uncertainty",
            "uncertainty_type",
            "sample_size",
            "unit",
            "conditions_cel",
            "statement",
            "expression",
            "sympy_generated",
            "sympy_error",
            "name",
            "measure",
            "listener_population",
            "methodology",
            "notes",
            "description",
            "auto_summary",
            "body",
            "canonical_ast",
            "variables_json",
            "stage",
            "source_slug",
            "source_quality_opinion",
            "source_paper",
            "source_id",
            "source_kind",
            "source_origin_type",
            "source_origin_value",
            "source_origin_retrieved",
            "source_origin_content_ref",
            "source_prior_base_rate",
            "source_quality_json",
            "source_derived_from_json",
            "provenance_page",
            "provenance_json",
            "value_si",
            "lower_bound_si",
            "upper_bound_si",
            "context_id",
            "source",
        }
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        artifact_id = row_map.get("artifact_id", row_map.get("id"))
        if artifact_id is None:
            raise KeyError("id")
        logical_id_entries = row_map.get("logical_ids")
        logical_ids_json = row_map.get("logical_ids_json")
        if logical_id_entries is None and isinstance(logical_ids_json, str) and logical_ids_json:
            try:
                logical_id_entries = json.loads(logical_ids_json)
            except json.JSONDecodeError:
                logical_id_entries = None
        logical_ids: list[LogicalId] = []
        if isinstance(logical_id_entries, list):
            for entry in logical_id_entries:
                if not isinstance(entry, Mapping):
                    continue
                namespace = entry.get("namespace")
                value = entry.get("value")
                if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
                    logical_ids.append(LogicalId(namespace=namespace, value=value))
        primary_logical_id = row_map.get("primary_logical_id", row_map.get("logical_id"))
        if not logical_ids and isinstance(primary_logical_id, str) and ":" in primary_logical_id:
            namespace, value = primary_logical_id.split(":", 1)
            if namespace and value:
                logical_ids.append(LogicalId(namespace=namespace, value=value))

        nested_source = row_map.get("source") if isinstance(row_map.get("source"), Mapping) else None
        quality_trust = (
            SourceTrust.from_mapping(
                {"quality": row_map.get("source_quality_json") or row_map.get("source_quality_opinion")}
            )
            if row_map.get("source_quality_json") is not None
            or row_map.get("source_quality_opinion") is not None
            else None
        )
        derived_from_trust = (
            SourceTrust.from_mapping(
                {"derived_from": row_map.get("source_derived_from_json")}
            )
            if row_map.get("source_derived_from_json") is not None
            else None
        )
        flat_source = ClaimSource(
            source_id=(None if row_map.get("source_id") is None else str(row_map["source_id"])),
            kind=(None if row_map.get("source_kind") is None else str(row_map["source_kind"])),
            slug=(None if row_map.get("source_slug") is None else str(row_map["source_slug"])),
            origin=SourceOrigin(
                origin_type=(
                    None
                    if row_map.get("source_origin_type") is None
                    else str(row_map["source_origin_type"])
                ),
                value=(
                    None
                    if row_map.get("source_origin_value") is None
                    else str(row_map["source_origin_value"])
                ),
                retrieved=(
                    None
                    if row_map.get("source_origin_retrieved") is None
                    else str(row_map["source_origin_retrieved"])
                ),
                content_ref=(
                    None
                    if row_map.get("source_origin_content_ref") is None
                    else str(row_map["source_origin_content_ref"])
                ),
            ),
            trust=SourceTrust(
                prior_base_rate=(
                    None
                    if row_map.get("source_prior_base_rate") is None
                    else float(row_map["source_prior_base_rate"])
                ),
                quality=None if quality_trust is None else quality_trust.quality,
                derived_from=(
                    ()
                    if derived_from_trust is None
                    else derived_from_trust.derived_from
                ),
            ),
        )
        source = ClaimSource.from_mapping(nested_source, slug=flat_source.slug)
        if source is None and not flat_source.is_empty:
            source = ClaimSource(
                source_id=flat_source.source_id,
                kind=flat_source.kind,
                slug=flat_source.slug,
                origin=None if flat_source.origin is None or flat_source.origin.is_empty else flat_source.origin,
                trust=None if flat_source.trust is None or flat_source.trust.is_empty else flat_source.trust,
            )
        elif source is not None:
            source = ClaimSource(
                source_id=source.source_id if source.source_id is not None else flat_source.source_id,
                kind=source.kind if source.kind is not None else flat_source.kind,
                slug=source.slug if source.slug is not None else flat_source.slug,
                origin=source.origin if source.origin is not None else (
                    None if flat_source.origin is None or flat_source.origin.is_empty else flat_source.origin
                ),
                trust=source.trust if source.trust is not None else (
                    None if flat_source.trust is None or flat_source.trust.is_empty else flat_source.trust
                ),
            )
        provenance = ClaimProvenance.from_components(
            paper=(
                None if row_map.get("source_paper") is None else str(row_map["source_paper"])
            ),
            page=(
                None if row_map.get("provenance_page") is None else int(row_map["provenance_page"])
            ),
            provenance_json=row_map.get("provenance_json"),
        )
        return cls(
            claim_id=to_claim_id(row_map["id"]),
            artifact_id=str(artifact_id),
            claim_type=(
                None
                if row_map.get("type", row_map.get("claim_type")) is None
                else coerce_claim_type(row_map.get("type", row_map.get("claim_type")))
            ),
            concept_id=(
                None if row_map.get("concept_id") is None else to_concept_id(row_map["concept_id"])
            ),
            target_concept=(
                None
                if row_map.get("target_concept") is None
                else to_concept_id(row_map["target_concept"])
            ),
            logical_ids=tuple(logical_ids),
            version_id=None if row_map.get("version_id") is None else str(row_map["version_id"]),
            seq=None if row_map.get("seq") is None else int(row_map["seq"]),
            value=row_map.get("value"),
            lower_bound=(
                None if row_map.get("lower_bound") is None else float(row_map["lower_bound"])
            ),
            upper_bound=(
                None if row_map.get("upper_bound") is None else float(row_map["upper_bound"])
            ),
            uncertainty=(
                None if row_map.get("uncertainty") is None else float(row_map["uncertainty"])
            ),
            uncertainty_type=(
                None if row_map.get("uncertainty_type") is None else str(row_map["uncertainty_type"])
            ),
            sample_size=(
                None if row_map.get("sample_size") is None else int(row_map["sample_size"])
            ),
            unit=None if row_map.get("unit") is None else str(row_map["unit"]),
            conditions_cel=(
                None if row_map.get("conditions_cel") is None else str(row_map["conditions_cel"])
            ),
            statement=None if row_map.get("statement") is None else str(row_map["statement"]),
            expression=None if row_map.get("expression") is None else str(row_map["expression"]),
            sympy_generated=(
                None if row_map.get("sympy_generated") is None else str(row_map["sympy_generated"])
            ),
            sympy_error=(
                None if row_map.get("sympy_error") is None else str(row_map["sympy_error"])
            ),
            name=None if row_map.get("name") is None else str(row_map["name"]),
            measure=None if row_map.get("measure") is None else str(row_map["measure"]),
            listener_population=(
                None
                if row_map.get("listener_population") is None
                else str(row_map["listener_population"])
            ),
            methodology=(
                None if row_map.get("methodology") is None else str(row_map["methodology"])
            ),
            notes=None if row_map.get("notes") is None else str(row_map["notes"]),
            description=(
                None if row_map.get("description") is None else str(row_map["description"])
            ),
            auto_summary=(
                None if row_map.get("auto_summary") is None else str(row_map["auto_summary"])
            ),
            body=None if row_map.get("body") is None else str(row_map["body"]),
            canonical_ast=(
                None if row_map.get("canonical_ast") is None else str(row_map["canonical_ast"])
            ),
            variables_json=(
                None if row_map.get("variables_json") is None else str(row_map["variables_json"])
            ),
            stage=None if row_map.get("stage") is None else str(row_map["stage"]),
            source=source,
            provenance=provenance,
            value_si=None if row_map.get("value_si") is None else float(row_map["value_si"]),
            lower_bound_si=(
                None if row_map.get("lower_bound_si") is None else float(row_map["lower_bound_si"])
            ),
            upper_bound_si=(
                None if row_map.get("upper_bound_si") is None else float(row_map["upper_bound_si"])
            ),
            context_id=(
                None if row_map.get("context_id") is None else to_context_id(row_map["context_id"])
            ),
            attributes=attributes,
        )

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    @property
    def primary_logical_value(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].value

    @property
    def source_paper(self) -> str | None:
        return None if self.provenance is None else self.provenance.paper

    @property
    def provenance_page(self) -> int | None:
        return None if self.provenance is None else self.provenance.page

    @property
    def source_slug(self) -> str | None:
        return None if self.source is None else self.source.slug

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.claim_id,
            "artifact_id": self.artifact_id,
        }
        logical_ids_payload = [logical_id.to_payload() for logical_id in self.logical_ids]
        logical_ids_json = json.dumps(logical_ids_payload) if logical_ids_payload else None
        source_dict = None if self.source is None or self.source.is_empty else self.source.to_dict()
        provenance_json = None if self.provenance is None else self.provenance.to_json()
        provenance_page = None if self.provenance is None else self.provenance.page
        source_paper = None if self.provenance is None else self.provenance.paper
        source_quality = (
            None
            if self.source is None or self.source.trust is None
            else self.source.trust.quality_dict()
        )
        source_derived_from = (
            None
            if self.source is None or self.source.trust is None or not self.source.trust.derived_from
            else json.dumps(list(self.source.trust.derived_from))
        )
        optional_fields = {
            "primary_logical_id": self.primary_logical_id,
            "version_id": self.version_id,
            "seq": self.seq,
            "type": self.claim_type,
            "concept_id": self.concept_id,
            "target_concept": self.target_concept,
            "value": self.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "uncertainty": self.uncertainty,
            "uncertainty_type": self.uncertainty_type,
            "sample_size": self.sample_size,
            "unit": self.unit,
            "conditions_cel": self.conditions_cel,
            "statement": self.statement,
            "expression": self.expression,
            "sympy_generated": self.sympy_generated,
            "sympy_error": self.sympy_error,
            "name": self.name,
            "measure": self.measure,
            "listener_population": self.listener_population,
            "methodology": self.methodology,
            "notes": self.notes,
            "description": self.description,
            "auto_summary": self.auto_summary,
            "body": self.body,
            "canonical_ast": self.canonical_ast,
            "variables_json": self.variables_json,
            "stage": self.stage,
            "source_slug": None if self.source is None else self.source.slug,
            "source_paper": source_paper,
            "source_id": None if self.source is None else self.source.source_id,
            "source_kind": (
                None
                if self.source is None or self.source.kind is None
                else self.source.kind.value
            ),
            "source_origin_type": (
                None
                if self.source is None
                or self.source.origin is None
                or self.source.origin.origin_type is None
                else self.source.origin.origin_type.value
            ),
            "source_origin_value": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.value
            ),
            "source_origin_retrieved": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.retrieved
            ),
            "source_origin_content_ref": (
                None
                if self.source is None or self.source.origin is None
                else self.source.origin.content_ref
            ),
            "source_prior_base_rate": (
                None
                if self.source is None or self.source.trust is None
                else self.source.trust.prior_base_rate
            ),
            "source_quality_json": (
                None if source_quality is None else json.dumps(source_quality)
            ),
            "source_derived_from_json": source_derived_from,
            "provenance_page": provenance_page,
            "provenance_json": provenance_json,
            "value_si": self.value_si,
            "lower_bound_si": self.lower_bound_si,
            "upper_bound_si": self.upper_bound_si,
            "context_id": self.context_id,
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value
        data["logical_id"] = self.primary_logical_id
        data["logical_ids"] = logical_ids_payload
        if source_dict is not None:
            data["source"] = source_dict
        if source_quality is not None:
            data["source_quality_opinion"] = source_quality
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class StanceRow:
    claim_id: ClaimId
    target_claim_id: ClaimId
    stance_type: StanceType
    target_justification_id: JustificationId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stance_type", coerce_stance_type(self.stance_type))
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> StanceRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"claim_id", "target_claim_id", "stance_type", "target_justification_id"}
            and value is not None
        }
        return cls(
            claim_id=to_claim_id(row_map["claim_id"]),
            target_claim_id=to_claim_id(row_map["target_claim_id"]),
            stance_type=coerce_stance_type(row_map["stance_type"]),
            target_justification_id=(
                None
                if row_map.get("target_justification_id") is None
                else to_justification_id(row_map["target_justification_id"])
            ),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "target_claim_id": self.target_claim_id,
            "stance_type": self.stance_type.value,
        }
        if self.target_justification_id is not None:
            data["target_justification_id"] = self.target_justification_id
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class ConflictRow:
    claim_a_id: ClaimId
    claim_b_id: ClaimId
    concept_id: ConceptId | None = None
    warning_class: ConflictClass | None = None
    conflict_class: ConflictClass | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "warning_class", coerce_conflict_class(self.warning_class))
        object.__setattr__(self, "conflict_class", coerce_conflict_class(self.conflict_class))
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
        }
        if self.concept_id is not None:
            data["concept_id"] = self.concept_id
        if self.warning_class is not None:
            data["warning_class"] = self.warning_class.value
        if self.conflict_class is not None:
            data["conflict_class"] = self.conflict_class.value
        data.update(self.attributes)
        return data

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ConflictRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"claim_a_id", "claim_b_id", "concept_id", "warning_class", "conflict_class"}
            and value is not None
        }
        return cls(
            claim_a_id=to_claim_id(row_map["claim_a_id"]),
            claim_b_id=to_claim_id(row_map["claim_b_id"]),
            concept_id=(
                None
                if row_map.get("concept_id") is None
                else to_concept_id(row_map["concept_id"])
            ),
            warning_class=coerce_conflict_class(row_map.get("warning_class")),
            conflict_class=coerce_conflict_class(row_map.get("conflict_class")),
            attributes=attributes,
        )


@dataclass(frozen=True)
class ParameterizationRow:
    output_concept_id: ConceptId
    concept_ids: str
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    conditions_cel: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "exactness", coerce_exactness(self.exactness))
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "output_concept_id": self.output_concept_id,
            "concept_ids": self.concept_ids,
        }
        if self.formula is not None:
            data["formula"] = self.formula
        if self.sympy is not None:
            data["sympy"] = self.sympy
        if self.exactness is not None:
            data["exactness"] = self.exactness.value
        if self.conditions_cel is not None:
            data["conditions_cel"] = self.conditions_cel
        data.update(self.attributes)
        return data

    @classmethod
    def from_mapping(
        cls,
        row_map: Mapping[str, Any],
        *,
        output_concept_id: ConceptId | str | None = None,
    ) -> ParameterizationRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"output_concept_id", "concept_ids", "formula", "sympy", "exactness", "conditions_cel"}
            and value is not None
        }
        resolved_output_concept_id = row_map.get("output_concept_id", output_concept_id)
        if resolved_output_concept_id is None:
            raise KeyError("output_concept_id")
        return cls(
            output_concept_id=to_concept_id(resolved_output_concept_id),
            concept_ids=str(row_map["concept_ids"]),
            formula=None if row_map.get("formula") is None else str(row_map["formula"]),
            sympy=None if row_map.get("sympy") is None else str(row_map["sympy"]),
            exactness=coerce_exactness(row_map.get("exactness")),
            conditions_cel=(
                None
                if row_map.get("conditions_cel") is None
                else str(row_map["conditions_cel"])
            ),
            attributes=attributes,
        )


ConceptRowInput = ConceptRow | Mapping[str, Any]
ClaimRowInput = ClaimRow | Mapping[str, Any]
RelationshipRowInput = RelationshipRow | Mapping[str, Any]
StanceRowInput = StanceRow | Mapping[str, Any]
ConflictRowInput = ConflictRow | Mapping[str, Any]
ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


def coerce_concept_row(row: ConceptRowInput) -> ConceptRow:
    if isinstance(row, ConceptRow):
        return row
    return ConceptRow.from_mapping(row)


def coerce_claim_row(row: ClaimRowInput) -> ClaimRow:
    if isinstance(row, ClaimRow):
        return row
    return ClaimRow.from_mapping(row)


def coerce_relationship_row(row: RelationshipRowInput) -> RelationshipRow:
    if isinstance(row, RelationshipRow):
        return row
    return RelationshipRow.from_mapping(row)


def coerce_stance_row(row: StanceRowInput) -> StanceRow:
    if isinstance(row, StanceRow):
        return row
    return StanceRow.from_mapping(row)


def coerce_conflict_row(row: ConflictRowInput) -> ConflictRow:
    if isinstance(row, ConflictRow):
        return row
    return ConflictRow.from_mapping(row)


def coerce_parameterization_row(
    row: ParameterizationRowInput,
    *,
    output_concept_id: ConceptId | str | None = None,
) -> ParameterizationRow:
    if isinstance(row, ParameterizationRow):
        return row
    return ParameterizationRow.from_mapping(
        row,
        output_concept_id=output_concept_id,
    )
