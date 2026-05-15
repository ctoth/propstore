"""Typed storage-row boundaries for stable sidecar shapes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.algorithm_stage import AlgorithmStage, coerce_algorithm_stage
from propstore.core.relations import (
    ClaimConceptLinkRole,
    coerce_claim_concept_link_role,
)
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.exactness_types import Exactness, coerce_exactness
from propstore.core.claim_values import (
    ClaimProvenance,
    ClaimSource,
    SourceOrigin,
    SourceTrust,
)
from propstore.core.source_types import coerce_source_kind, coerce_source_origin_type
from propstore.core.id_types import (
    ConceptId,
    ContextId,
    LogicalId,
    to_concept_id,
    to_context_id,
)


def _require_claim_type(value: object) -> ClaimType:
    claim_type = coerce_claim_type(value)
    if claim_type is None:
        raise KeyError("claim_type")
    return claim_type


def _require_claim_concept_link_role(value: object) -> ClaimConceptLinkRole:
    role = coerce_claim_concept_link_role(value)
    if role is None:
        raise KeyError("role")
    return role


@dataclass(frozen=True)
class ParameterizationRow:
    output_concept_id: ConceptId
    concept_ids: str
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    conditions_cel: str | None = None
    conditions_ir: str | None = None
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
        if self.conditions_ir is not None:
            data["conditions_ir"] = self.conditions_ir
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
            if key not in {"output_concept_id", "concept_ids", "formula", "sympy", "exactness", "conditions_cel", "conditions_ir"}
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
            conditions_ir=(
                None
                if row_map.get("conditions_ir") is None
                else str(row_map["conditions_ir"])
            ),
            attributes=attributes,
        )


ParameterizationRowInput = ParameterizationRow | Mapping[str, Any]


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
