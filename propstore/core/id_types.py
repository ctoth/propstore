"""Semantic ID newtypes for the value/honesty layer.

These are ``NewType`` brands over ``str`` so the type checker keeps a situated
*assertion* identity distinct from a bare string without introducing a runtime
wrapper. Only the identities the Phase-5a value layer needs live here; the wider
id family is grown by later phases as their callers arrive.

Phase 7 (world layer) adds :data:`AssumptionId` and :data:`QueryableId` — the ATMS
assumption brand and the fragility/queryable handle brand — plus the iterable
coercers (``to_*_ids``) the compiled-graph carriers need.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import NewType

AssertionId = NewType("AssertionId", str)
ClaimId = NewType("ClaimId", str)
ConceptId = NewType("ConceptId", str)
ContextId = NewType("ContextId", str)
ConditionId = NewType("ConditionId", str)
ProvenanceGraphId = NewType("ProvenanceGraphId", str)
AssumptionId = NewType("AssumptionId", str)
QueryableId = NewType("QueryableId", str)


def to_assertion_id(value: object) -> AssertionId:
    """Brand an arbitrary value's string form as an :data:`AssertionId`."""

    return AssertionId(str(value))


def to_concept_id(value: object) -> ConceptId:
    """Brand an arbitrary value's string form as a :data:`ConceptId`."""

    return ConceptId(str(value))


def to_claim_id(value: object) -> ClaimId:
    """Brand an arbitrary value's string form as a :data:`ClaimId`."""

    return ClaimId(str(value))


def to_context_id(value: object) -> ContextId:
    """Brand an arbitrary value's string form as a :data:`ContextId`."""

    return ContextId(str(value))


def to_condition_id(value: object) -> ConditionId:
    """Brand an arbitrary value's string form as a :data:`ConditionId`."""

    return ConditionId(str(value))


def to_provenance_graph_id(value: object) -> ProvenanceGraphId:
    """Brand an arbitrary value's string form as a :data:`ProvenanceGraphId`."""

    return ProvenanceGraphId(str(value))


def to_assumption_id(value: object) -> AssumptionId:
    """Brand an arbitrary value's string form as an :data:`AssumptionId`."""

    return AssumptionId(str(value))


def to_queryable_id(value: object) -> QueryableId:
    """Brand an arbitrary value's string form as a :data:`QueryableId`."""

    return QueryableId(str(value))


def to_concept_ids(values: Iterable[object]) -> tuple[ConceptId, ...]:
    """Brand each value's string form as a :data:`ConceptId`."""

    return tuple(to_concept_id(value) for value in values)


def to_claim_ids(values: Iterable[object]) -> tuple[ClaimId, ...]:
    """Brand each value's string form as a :data:`ClaimId`."""

    return tuple(to_claim_id(value) for value in values)


def to_assumption_ids(values: Iterable[object]) -> tuple[AssumptionId, ...]:
    """Brand each value's string form as an :data:`AssumptionId`."""

    return tuple(to_assumption_id(value) for value in values)


def to_queryable_ids(values: Iterable[object]) -> tuple[QueryableId, ...]:
    """Brand each value's string form as a :data:`QueryableId`."""

    return tuple(to_queryable_id(value) for value in values)
