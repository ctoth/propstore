"""Semantic ID newtypes and coercion helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NewType

ConceptId = NewType("ConceptId", str)
ClaimId = NewType("ClaimId", str)
ContextId = NewType("ContextId", str)
JustificationId = NewType("JustificationId", str)
AssumptionId = NewType("AssumptionId", str)
QueryableId = NewType("QueryableId", str)


def to_concept_id(value: object) -> ConceptId:
    return ConceptId(str(value))


def to_claim_id(value: object) -> ClaimId:
    return ClaimId(str(value))


def to_context_id(value: object) -> ContextId:
    return ContextId(str(value))


def to_justification_id(value: object) -> JustificationId:
    return JustificationId(str(value))


def to_assumption_id(value: object) -> AssumptionId:
    return AssumptionId(str(value))


def to_queryable_id(value: object) -> QueryableId:
    return QueryableId(str(value))


def to_concept_ids(values: Iterable[object]) -> tuple[ConceptId, ...]:
    return tuple(to_concept_id(value) for value in values)


def to_claim_ids(values: Iterable[object]) -> tuple[ClaimId, ...]:
    return tuple(to_claim_id(value) for value in values)


def to_assumption_ids(values: Iterable[object]) -> tuple[AssumptionId, ...]:
    return tuple(to_assumption_id(value) for value in values)


def to_queryable_ids(values: Iterable[object]) -> tuple[QueryableId, ...]:
    return tuple(to_queryable_id(value) for value in values)
