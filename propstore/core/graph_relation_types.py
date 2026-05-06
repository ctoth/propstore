from __future__ import annotations

from enum import StrEnum


class GraphRelationType(StrEnum):
    BROADER = "broader"
    NARROWER = "narrower"
    RELATED = "related"
    COMPONENT_OF = "component_of"
    DERIVED_FROM = "derived_from"
    CONTESTED_DEFINITION = "contested_definition"
    IS_A = "is_a"
    PART_OF = "part_of"
    KIND_OF = "kind_of"
    REBUTS = "rebuts"
    UNDERCUTS = "undercuts"
    UNDERMINES = "undermines"
    SUPPORTS = "supports"
    EXPLAINS = "explains"
    SUPERSEDES = "supersedes"
    NONE = "none"


VALID_GRAPH_RELATION_TYPES = frozenset(relation_type.value for relation_type in GraphRelationType)


def coerce_graph_relation_type(value: object) -> GraphRelationType:
    if isinstance(value, GraphRelationType):
        return value
    if isinstance(value, str):
        try:
            return GraphRelationType(value)
        except ValueError as exc:
            raise ValueError(
                "Unsupported graph relation type "
                f"{value!r}. Expected one of: {', '.join(sorted(VALID_GRAPH_RELATION_TYPES))}"
            ) from exc
    raise TypeError(f"Unsupported graph relation type: {type(value).__name__}")
