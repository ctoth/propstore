"""Canonical concept-to-concept relationship vocabulary."""

from __future__ import annotations

from enum import StrEnum


class ConceptRelationshipType(StrEnum):
    BROADER = "broader"
    NARROWER = "narrower"
    RELATED = "related"
    COMPONENT_OF = "component_of"
    DERIVED_FROM = "derived_from"
    CONTESTED_DEFINITION = "contested_definition"
    IS_A = "is_a"
    PART_OF = "part_of"
    KIND_OF = "kind_of"


VALID_CONCEPT_RELATIONSHIP_TYPES = frozenset(
    relationship_type.value
    for relationship_type in ConceptRelationshipType
)


def coerce_concept_relationship_type(
    value: object | None,
) -> ConceptRelationshipType | None:
    if value is None:
        return None
    if isinstance(value, ConceptRelationshipType):
        return value
    return ConceptRelationshipType(str(value))
