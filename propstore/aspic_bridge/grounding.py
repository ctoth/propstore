"""Grounded-rule projection for the ASPIC+ bridge.

A grounded-rules bundle (the gunray datalog result) projects into ASPIC+ rules,
axioms, and a rule-superiority order. The full gunray-inspection → ASPIC+
translation is a dedicated sub-slice; what lands here is the *empty-bundle* path
the non-grounded bridge and the CKR integration rely on, plus the projection
value type. A non-empty bundle raises rather than silently dropping its rules
(CLAUDE.md non-commitment: nothing is filtered away quietly).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from argumentation.structured.aspic.aspic import KnowledgeBase, Literal, Rule
from argumentation.structured.aspic.datalog_grounding import GroundRuleOrigin

from propstore.core.literal_keys import LiteralKey
from propstore.grounding.bundle import GroundedRulesBundle


@dataclass(frozen=True)
class GroundedAspicProjection:
    """The ASPIC+ projection of a grounded-rules bundle."""

    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]
    literals: dict[LiteralKey, Literal]
    origins: Mapping[Rule, GroundRuleOrigin]
    rule_order: frozenset[tuple[Rule, Rule]]


def _bundle_is_empty(bundle: GroundedRulesBundle) -> bool:
    return not bundle.source_rules and not bundle.source_facts and bundle.arguments == ()


def _deferred(bundle: GroundedRulesBundle) -> None:
    if not _bundle_is_empty(bundle):
        raise NotImplementedError(
            "grounded-rule → ASPIC+ projection is not yet implemented for non-empty "
            "bundles; the gunray-inspection translation is a dedicated sub-slice"
        )


def project_grounded_rules(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    *,
    complement_encoder: object | None = None,
) -> GroundedAspicProjection:
    """Project a grounded bundle into ASPIC+ rules (empty-bundle path)."""

    _deferred(bundle)
    return GroundedAspicProjection(
        strict_rules=frozenset(),
        defeasible_rules=frozenset(),
        literals=dict(literals),
        origins={},
        rule_order=frozenset(),
    )


def ground_facts_to_axioms(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    kb: KnowledgeBase,
    *,
    complement_encoder: object | None = None,
) -> KnowledgeBase:
    """Fold grounded facts into ``K_n`` (empty-bundle path leaves ``kb`` as-is)."""

    _deferred(bundle)
    return kb


__all__ = ["GroundedAspicProjection", "ground_facts_to_axioms", "project_grounded_rules"]
