"""Typed claim surface for repository merge semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from propstore.core.assertions.situated import derive_assertion_id
from propstore.core.id_types import AssertionId
from propstore.families.claims.declaration import (
    ClaimDocument,
    claim_logical_id_formatted,
)


@dataclass(frozen=True)
class MergeClaim:
    document: ClaimDocument
    branch_origin: str | None = None

    @property
    def artifact_id(self) -> str:
        assert self.document.artifact_id is not None
        return self.document.artifact_id

    @property
    def claim_type(self) -> str | None:
        return self.document.type

    @property
    def value_concept_id(self) -> str:
        if (
            isinstance(self.document.output_concept, str)
            and self.document.output_concept
        ):
            return self.document.output_concept
        if (
            isinstance(self.document.target_concept, str)
            and self.document.target_concept
        ):
            return self.document.target_concept
        for concept_id in self.document.concepts:
            if isinstance(concept_id, str) and concept_id:
                return concept_id
        return ""

    @property
    def primary_logical_id(self) -> str | None:
        logical_ids = self.logical_ids
        if logical_ids:
            return logical_ids[0]
        return None

    @property
    def value(self) -> Any:
        return self.document.value

    @property
    def source_paper(self) -> str | None:
        if self.document.source is not None:
            return self.document.source.paper
        if self.document.provenance is not None:
            return self.document.provenance.paper
        return None

    @property
    def source_page(self) -> int | None:
        if self.document.provenance is not None:
            return self.document.provenance.page
        return None

    @property
    def logical_ids(self) -> tuple[str, ...]:
        return tuple(
            claim_logical_id_formatted(logical_id)
            for logical_id in self.document.logical_ids
        )

    @property
    def assertion_id(self) -> AssertionId:
        return derive_assertion_id(
            ("merge_claim", self.artifact_id, self.branch_origin, self.semantic_key())
        )

    def semantic_key(self) -> tuple[object, ...]:
        document = self.document
        context_id = None if document.context is None else str(document.context.id)
        return (
            _enum_value(document.type),
            context_id,
            document.body,
            tuple(str(concept) for concept in document.concepts),
            tuple(str(condition) for condition in document.conditions),
            document.expression,
            document.listener_population,
            document.lower_bound,
            document.measure,
            document.output_concept,
            tuple(
                (parameter.name, parameter.concept, parameter.note)
                for parameter in document.parameters
            ),
            document.sample_size,
            _enum_value(document.stage),
            document.statement,
            document.sympy,
            document.target_concept,
            document.uncertainty,
            document.uncertainty_type,
            document.unit,
            document.upper_bound,
            document.value,
            tuple(
                (variable.concept, variable.symbol, variable.role, variable.name)
                for variable in document.variables
            ),
        )


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def _digest(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()
