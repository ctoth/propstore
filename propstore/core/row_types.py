"""Typed storage-row boundaries for stable sidecar shapes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    ContextId,
    JustificationId,
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
    relation_type: str
    conditions_cel: str | None = None
    note: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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
            relation_type=str(relation_type),
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
            "type": self.relation_type,
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
    claim_type: str | None = None
    concept_id: ConceptId | None = None
    target_concept: ConceptId | None = None
    primary_logical_id: str | None = None
    logical_ids_json: str | None = None
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
    source_slug: str | None = None
    source_paper: str | None = None
    source_id: str | None = None
    source_kind: str | None = None
    source_origin_type: str | None = None
    source_origin_value: str | None = None
    source_origin_retrieved: str | None = None
    source_origin_content_ref: str | None = None
    source_prior_base_rate: float | None = None
    source_quality_json: str | None = None
    source_derived_from_json: str | None = None
    provenance_page: int | None = None
    provenance_json: str | None = None
    value_si: float | None = None
    lower_bound_si: float | None = None
    upper_bound_si: float | None = None
    context_id: ContextId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

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
            "logical_ids_json",
            "logical_ids",
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
            "source_paper",
            "source_id",
            "source_kind",
            "source_origin_type",
            "source_origin_value",
            "source_origin_retrieved",
            "source_origin_content_ref",
            "source_prior_base_rate",
            "source_quality_json",
            "source_quality_opinion",
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
        source = row_map.get("source")
        source_origin = source.get("origin") if isinstance(source, Mapping) else None
        source_trust = source.get("trust") if isinstance(source, Mapping) else None
        logical_ids_json = row_map.get("logical_ids_json")
        if logical_ids_json is None and isinstance(row_map.get("logical_ids"), list):
            logical_ids_json = json.dumps(row_map["logical_ids"])
        source_quality_json = row_map.get("source_quality_json")
        if source_quality_json is None:
            quality = row_map.get("source_quality_opinion")
            if quality is None and isinstance(source_trust, Mapping):
                quality = source_trust.get("quality")
            if isinstance(quality, Mapping):
                source_quality_json = json.dumps(dict(quality))
        source_derived_from_json = row_map.get("source_derived_from_json")
        if source_derived_from_json is None and isinstance(source_trust, Mapping):
            derived_from = source_trust.get("derived_from")
            if isinstance(derived_from, list):
                source_derived_from_json = json.dumps(derived_from)
        artifact_id = row_map.get("artifact_id", row_map.get("id"))
        if artifact_id is None:
            raise KeyError("id")
        source_id = row_map.get("source_id")
        if source_id is None and isinstance(source, Mapping):
            source_id = source.get("id")
        source_kind = row_map.get("source_kind")
        if source_kind is None and isinstance(source, Mapping):
            source_kind = source.get("kind")
        source_origin_type = row_map.get("source_origin_type")
        if source_origin_type is None and isinstance(source_origin, Mapping):
            source_origin_type = source_origin.get("type")
        source_origin_value = row_map.get("source_origin_value")
        if source_origin_value is None and isinstance(source_origin, Mapping):
            source_origin_value = source_origin.get("value")
        source_origin_retrieved = row_map.get("source_origin_retrieved")
        if source_origin_retrieved is None and isinstance(source_origin, Mapping):
            source_origin_retrieved = source_origin.get("retrieved")
        source_origin_content_ref = row_map.get("source_origin_content_ref")
        if source_origin_content_ref is None and isinstance(source_origin, Mapping):
            source_origin_content_ref = source_origin.get("content_ref")
        source_prior_base_rate = row_map.get("source_prior_base_rate")
        if source_prior_base_rate is None and isinstance(source_trust, Mapping):
            source_prior_base_rate = source_trust.get("prior_base_rate")
        return cls(
            claim_id=to_claim_id(row_map["id"]),
            artifact_id=str(artifact_id),
            claim_type=(
                None
                if row_map.get("type", row_map.get("claim_type")) is None
                else str(row_map.get("type", row_map.get("claim_type")))
            ),
            concept_id=(
                None if row_map.get("concept_id") is None else to_concept_id(row_map["concept_id"])
            ),
            target_concept=(
                None
                if row_map.get("target_concept") is None
                else to_concept_id(row_map["target_concept"])
            ),
            primary_logical_id=(
                None
                if row_map.get("primary_logical_id", row_map.get("logical_id")) is None
                else str(row_map.get("primary_logical_id", row_map.get("logical_id")))
            ),
            logical_ids_json=None if logical_ids_json is None else str(logical_ids_json),
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
            source_slug=None if row_map.get("source_slug") is None else str(row_map["source_slug"]),
            source_paper=(
                None if row_map.get("source_paper") is None else str(row_map["source_paper"])
            ),
            source_id=None if source_id is None else str(source_id),
            source_kind=None if source_kind is None else str(source_kind),
            source_origin_type=(
                None if source_origin_type is None else str(source_origin_type)
            ),
            source_origin_value=(
                None if source_origin_value is None else str(source_origin_value)
            ),
            source_origin_retrieved=(
                None if source_origin_retrieved is None else str(source_origin_retrieved)
            ),
            source_origin_content_ref=(
                None if source_origin_content_ref is None else str(source_origin_content_ref)
            ),
            source_prior_base_rate=(
                None if source_prior_base_rate is None else float(source_prior_base_rate)
            ),
            source_quality_json=(
                None if source_quality_json is None else str(source_quality_json)
            ),
            source_derived_from_json=(
                None if source_derived_from_json is None else str(source_derived_from_json)
            ),
            provenance_page=(
                None if row_map.get("provenance_page") is None else int(row_map["provenance_page"])
            ),
            provenance_json=(
                None if row_map.get("provenance_json") is None else str(row_map["provenance_json"])
            ),
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

    def parsed_logical_ids(self) -> list[dict[str, Any]]:
        if not self.logical_ids_json:
            return []
        try:
            loaded = json.loads(self.logical_ids_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def parsed_source_quality(self) -> Mapping[str, Any] | None:
        if not self.source_quality_json:
            return None
        try:
            loaded = json.loads(self.source_quality_json)
        except json.JSONDecodeError:
            return None
        return dict(loaded) if isinstance(loaded, Mapping) else None

    def parsed_source_derived_from(self) -> list[Any]:
        if not self.source_derived_from_json:
            return []
        try:
            loaded = json.loads(self.source_derived_from_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def source_dict(self) -> dict[str, Any] | None:
        if not any(
            value is not None
            for value in (
                self.source_id,
                self.source_kind,
                self.source_origin_type,
                self.source_origin_value,
                self.source_origin_retrieved,
                self.source_origin_content_ref,
                self.source_prior_base_rate,
                self.source_quality_json,
                self.source_derived_from_json,
            )
        ):
            return None
        quality = self.parsed_source_quality()
        return {
            "id": self.source_id,
            "kind": self.source_kind,
            "origin": {
                "type": self.source_origin_type,
                "value": self.source_origin_value,
                "retrieved": self.source_origin_retrieved,
                "content_ref": self.source_origin_content_ref,
            },
            "trust": {
                "prior_base_rate": self.source_prior_base_rate,
                "quality": quality,
                "derived_from": self.parsed_source_derived_from(),
            },
        }

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.claim_id,
            "artifact_id": self.artifact_id,
        }
        optional_fields = {
            "primary_logical_id": self.primary_logical_id,
            "logical_ids_json": self.logical_ids_json,
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
            "source_slug": self.source_slug,
            "source_paper": self.source_paper,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "source_origin_type": self.source_origin_type,
            "source_origin_value": self.source_origin_value,
            "source_origin_retrieved": self.source_origin_retrieved,
            "source_origin_content_ref": self.source_origin_content_ref,
            "source_prior_base_rate": self.source_prior_base_rate,
            "source_quality_json": self.source_quality_json,
            "source_derived_from_json": self.source_derived_from_json,
            "provenance_page": self.provenance_page,
            "provenance_json": self.provenance_json,
            "value_si": self.value_si,
            "lower_bound_si": self.lower_bound_si,
            "upper_bound_si": self.upper_bound_si,
            "context_id": self.context_id,
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value
        data["logical_id"] = self.primary_logical_id
        data["logical_ids"] = self.parsed_logical_ids()
        source = self.source_dict()
        if source is not None:
            data["source"] = source
            quality = source["trust"].get("quality")
            if quality is not None:
                data["source_quality_opinion"] = quality
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class StanceRow:
    claim_id: ClaimId
    target_claim_id: ClaimId
    stance_type: str
    target_justification_id: JustificationId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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
            stance_type=str(row_map["stance_type"]),
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
            "stance_type": self.stance_type,
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
    warning_class: str | None = None
    conflict_class: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
        }
        if self.concept_id is not None:
            data["concept_id"] = self.concept_id
        if self.warning_class is not None:
            data["warning_class"] = self.warning_class
        if self.conflict_class is not None:
            data["conflict_class"] = self.conflict_class
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
            warning_class=None if row_map.get("warning_class") is None else str(row_map["warning_class"]),
            conflict_class=None if row_map.get("conflict_class") is None else str(row_map["conflict_class"]),
            attributes=attributes,
        )


@dataclass(frozen=True)
class ParameterizationRow:
    output_concept_id: ConceptId
    concept_ids: str
    formula: str | None = None
    sympy: str | None = None
    exactness: str | None = None
    conditions_cel: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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
            data["exactness"] = self.exactness
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
            exactness=None if row_map.get("exactness") is None else str(row_map["exactness"]),
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
