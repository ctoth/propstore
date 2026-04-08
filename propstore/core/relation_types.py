"""Canonical stance-relation categories shared across argumentation layers.

These names are backend-agnostic. They classify relation-edge semantics, not
the ownership of any particular claim-graph, ASPIC, or probabilistic module.
"""

from __future__ import annotations

ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})
UNCONDITIONAL_ATTACK_TYPES = frozenset({"undercuts", "supersedes"})
PREFERENCE_SENSITIVE_ATTACK_TYPES = frozenset({"rebuts", "undermines"})
SUPPORT_TYPES = frozenset({"supports", "explains"})
NON_ATTACK_TYPES = frozenset({"supports", "explains", "none"})
GRAPH_RELATION_TYPES = ATTACK_TYPES | SUPPORT_TYPES
