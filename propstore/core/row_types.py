"""Typed storage-row boundaries for stable sidecar shapes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StanceRow:
    claim_id: str
    target_claim_id: str
    stance_type: str
    target_justification_id: str | None = None
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
            claim_id=str(row_map["claim_id"]),
            target_claim_id=str(row_map["target_claim_id"]),
            stance_type=str(row_map["stance_type"]),
            target_justification_id=(
                None
                if row_map.get("target_justification_id") is None
                else str(row_map["target_justification_id"])
            ),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
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
    claim_a_id: str
    claim_b_id: str
    concept_id: str | None = None
    warning_class: str | None = None
    conflict_class: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data = {
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
            claim_a_id=str(row_map["claim_a_id"]),
            claim_b_id=str(row_map["claim_b_id"]),
            concept_id=None if row_map.get("concept_id") is None else str(row_map["concept_id"]),
            warning_class=None if row_map.get("warning_class") is None else str(row_map["warning_class"]),
            conflict_class=None if row_map.get("conflict_class") is None else str(row_map["conflict_class"]),
            attributes=attributes,
        )


@dataclass(frozen=True)
class ParameterizationRow:
    output_concept_id: str
    concept_ids: str
    formula: str | None = None
    sympy: str | None = None
    exactness: str | None = None
    conditions_cel: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data = {
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
    ) -> ParameterizationRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"output_concept_id", "concept_ids", "formula", "sympy", "exactness", "conditions_cel"}
            and value is not None
        }
        return cls(
            output_concept_id=str(row_map["output_concept_id"]),
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


StanceRowInput = StanceRow | Mapping[str, Any]
ConflictRowInput = ConflictRow | Mapping[str, Any]
ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


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
) -> ParameterizationRow:
    if isinstance(row, ParameterizationRow):
        return row
    return ParameterizationRow.from_mapping(row)
