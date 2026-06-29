"""Grounded-rule projection for the ASPIC+ bridge.

A grounded-rules bundle (the gunray datalog result) projects into ASPIC+ rules,
axioms, and a rule-superiority order. The translation itself lives in the
argumentation package's ``datalog_grounding`` module: propstore hands its
``gunray.GroundingInspection`` to ``grounding_inspection_to_aspic`` and uses the
returned ``GroundedDatalogTheory`` directly (CLAUDE.md substrate boundary — no
mirror type, no coercer). An empty bundle (no inspection and no source
rules/facts) projects to empty rule sets; a bundle that carries source rules or
facts but no inspection is an error rather than a silent drop (CLAUDE.md
non-commitment: nothing is filtered away quietly).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from argumentation.structured.aspic.aspic import KnowledgeBase, Literal, Rule
from argumentation.structured.aspic.datalog_grounding import (
    GroundedDatalogTheory,
    GroundRuleOrigin,
    grounding_inspection_to_aspic,
)

from propstore.core.literal_keys import LiteralKey, ground_key
from propstore.grounding.bundle import GroundedRulesBundle


@dataclass(frozen=True)
class GroundedAspicProjection:
    """The ASPIC+ projection of a grounded-rules bundle."""

    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]
    literals: dict[LiteralKey, Literal]
    origins: Mapping[Rule, GroundRuleOrigin]
    rule_order: frozenset[tuple[Rule, Rule]]


def typed_scalar_key(value: object) -> dict[str, object]:
    """Render a scalar as a typed, JSON-stable key fragment.

    Booleans, ints, floats, and strings are distinguished so that, e.g., the
    grounded constant ``1`` and the string ``"1"`` never alias to the same
    projected literal id downstream.
    """

    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": str(value)}


def _source_superiority(
    bundle: GroundedRulesBundle,
) -> tuple[tuple[str, str], ...]:
    """The authored ``superior > inferior`` pairs the bundle carries."""

    return tuple(
        (superiority.superior_rule_id, superiority.inferior_rule_id)
        for superiority in bundle.source_superiority
    )


def _project_bundle(bundle: GroundedRulesBundle) -> GroundedDatalogTheory | None:
    """Project the bundle's gunray inspection into a ``GroundedDatalogTheory``.

    Returns ``None`` for an empty bundle (no inspection, no source rules/facts).
    A bundle that carries source rules or facts but no inspection cannot be
    grounded and is rejected rather than silently dropped.
    """

    inspection = bundle.grounding_inspection
    if inspection is not None:
        return grounding_inspection_to_aspic(
            inspection,
            superiority=_source_superiority(bundle),
        )
    if not bundle.source_rules and not bundle.source_facts:
        return None
    raise ValueError(
        "GroundedRulesBundle must carry gunray grounding_inspection for ASPIC projection"
    )


def _extend_literals(
    literals: dict[LiteralKey, Literal],
    rules: frozenset[Rule],
    axioms: frozenset[Literal],
) -> dict[LiteralKey, Literal]:
    """Intern every grounded literal under its canonical structural key.

    Existing entries are never displaced (Modgil & Prakken 2018, Def 1, p.8: the
    language ``L`` grows but does not lose members), so claim-id literals minted
    upstream remain reachable after grounding.
    """

    for literal in axioms:
        literals.setdefault(ground_key(literal.atom, literal.negated), literal)
    for rule in rules:
        literals.setdefault(
            ground_key(rule.consequent.atom, rule.consequent.negated),
            rule.consequent,
        )
        for antecedent in rule.antecedents:
            literals.setdefault(
                ground_key(antecedent.atom, antecedent.negated),
                antecedent,
            )
    return literals


def project_grounded_rules(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    *,
    complement_encoder: object | None = None,
) -> GroundedAspicProjection:
    """Project a grounded bundle into ASPIC+ rules.

    The projection lives in ``argumentation.datalog_grounding``; propstore only
    supplies its bundle envelope and keeps the literal-key dictionary current for
    downstream projection code.
    """

    del complement_encoder
    grounded = _project_bundle(bundle)
    if grounded is None:
        return GroundedAspicProjection(
            strict_rules=frozenset(),
            defeasible_rules=frozenset(),
            literals=dict(literals),
            origins={},
            rule_order=frozenset(),
        )
    strict_rules = grounded.system.strict_rules
    defeasible_rules = grounded.system.defeasible_rules
    return GroundedAspicProjection(
        strict_rules=strict_rules,
        defeasible_rules=defeasible_rules,
        literals=_extend_literals(
            literals, strict_rules | defeasible_rules, grounded.kb.axioms
        ),
        origins=grounded.rule_origins,
        rule_order=grounded.pref.rule_order,
    )


def ground_facts_to_axioms(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    kb: KnowledgeBase,
    *,
    complement_encoder: object | None = None,
) -> KnowledgeBase:
    """Fold grounded facts into ``K_n`` (empty-bundle path leaves ``kb`` as-is)."""

    del complement_encoder
    grounded = _project_bundle(bundle)
    if grounded is None:
        return kb
    _extend_literals(literals, frozenset(), grounded.kb.axioms)
    return KnowledgeBase(
        axioms=kb.axioms | grounded.kb.axioms,
        premises=kb.premises,
    )


__all__ = [
    "GroundedAspicProjection",
    "ground_facts_to_axioms",
    "project_grounded_rules",
    "typed_scalar_key",
]
