"""Canonical relation-edge vocabulary for the compiled world graph.

The compiled world graph (:mod:`propstore.core.graph_types`) carries both
concept-to-concept relationships and claim-to-claim stances as
:class:`~propstore.core.graph_types.RelationEdge` objects; their kind is one of
:class:`GraphRelationType`. :func:`coerce_graph_relation_type` is a validating
deserialization narrower (the family ``_coerce_kind`` shape), not a cross-package
coercer.
"""

from __future__ import annotations

from enum import StrEnum


class GraphRelationType(StrEnum):
    """The kind of edge in the compiled world graph."""

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


VALID_GRAPH_RELATION_TYPES = frozenset(
    relation_type.value for relation_type in GraphRelationType
)


def coerce_graph_relation_type(value: object) -> GraphRelationType:
    """Narrow a stored value to :class:`GraphRelationType`.

    Raises ``ValueError`` for an unknown string and ``TypeError`` for a
    non-string, non-enum value so an unrecognized relation never silently
    becomes a default.
    """

    if isinstance(value, GraphRelationType):
        return value
    if isinstance(value, str):
        try:
            return GraphRelationType(value)
        except ValueError as exc:
            raise ValueError(
                "Unsupported graph relation type "
                f"{value!r}. Expected one of: "
                f"{', '.join(sorted(VALID_GRAPH_RELATION_TYPES))}"
            ) from exc
    raise TypeError(f"Unsupported graph relation type: {type(value).__name__}")
