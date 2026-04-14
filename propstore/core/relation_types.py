"""Canonical stance-relation categories shared across argumentation layers.

These names are backend-agnostic. They classify relation-edge semantics, not
the ownership of any particular claim-graph, ASPIC, or probabilistic module.
"""

from __future__ import annotations

from propstore.core.graph_relation_types import GraphRelationType

ATTACK_TYPES = frozenset({
    GraphRelationType.REBUTS,
    GraphRelationType.UNDERCUTS,
    GraphRelationType.UNDERMINES,
    GraphRelationType.SUPERSEDES,
})
UNCONDITIONAL_ATTACK_TYPES = frozenset({
    GraphRelationType.UNDERCUTS,
    GraphRelationType.SUPERSEDES,
})
PREFERENCE_SENSITIVE_ATTACK_TYPES = frozenset({
    GraphRelationType.REBUTS,
    GraphRelationType.UNDERMINES,
})
SUPPORT_TYPES = frozenset({
    GraphRelationType.SUPPORTS,
    GraphRelationType.EXPLAINS,
})
NON_ATTACK_TYPES = frozenset({
    GraphRelationType.SUPPORTS,
    GraphRelationType.EXPLAINS,
    GraphRelationType.NONE,
})
GRAPH_RELATION_TYPES = ATTACK_TYPES | SUPPORT_TYPES
