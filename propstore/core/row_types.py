"""Typed storage-row boundaries for stable sidecar shapes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    JustificationId,
    to_claim_id,
    to_concept_id,
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
RelationshipRowInput = RelationshipRow | Mapping[str, Any]
StanceRowInput = StanceRow | Mapping[str, Any]
ConflictRowInput = ConflictRow | Mapping[str, Any]
ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


def coerce_concept_row(row: ConceptRowInput) -> ConceptRow:
    if isinstance(row, ConceptRow):
        return row
    return ConceptRow.from_mapping(row)


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
