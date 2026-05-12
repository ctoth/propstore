"""Grounded-rule projection for the ASPIC bridge."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from argumentation.aspic import (
    ArgumentationSystem,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    Rule,
)
from argumentation.datalog_grounding import (
    GroundRuleOrigin,
    GroundedDatalogTheory,
    grounding_inspection_to_aspic,
)
from propstore.core.literal_keys import LiteralKey, ground_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.complement import ComplementEncoder

_GroundFactKey = tuple[str, bool]


@dataclass(frozen=True)
class GroundedAspicProjection:
    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]
    literals: dict[LiteralKey, Literal]
    origins: Mapping[Rule, GroundRuleOrigin]
    rule_order: frozenset[tuple[Rule, Rule]]


def _typed_scalar_key(value: object) -> dict[str, object]:
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": str(value)}


def _canonical_substitution_key(sigma: Mapping[str, object]) -> str:
    """Render a substitution as a stable structured string."""

    return json.dumps(
        {name: _typed_scalar_key(sigma[name]) for name in sorted(sigma)},
        sort_keys=True,
        separators=(",", ":"),
    )


def _literal_for_atom(
    ground_atom: GroundAtom,
    negated: bool,
    literals: dict[LiteralKey, Literal],
) -> Literal:
    """Fetch or create the canonical literal for a grounded atom."""

    key = ground_key(ground_atom, negated)
    if key in literals:
        return literals[key]
    literal = Literal(atom=ground_atom, negated=negated)
    literals[key] = literal
    return literal


def _decode_grounded_predicate(
    predicate_id: str,
    complement_encoder: ComplementEncoder,
) -> _GroundFactKey:
    """Decode the grounded predicate convention into typed polarity."""

    toggled = complement_encoder.complement(predicate_id)
    negated = len(toggled) < len(predicate_id)
    positive = toggled if negated else predicate_id
    return positive, negated


def _source_superiority(
    bundle: GroundedRulesBundle,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (document.superior_rule_id, document.inferior_rule_id)
        for document in bundle.source_superiority
    )


def _project_bundle(bundle: GroundedRulesBundle) -> GroundedDatalogTheory:
    inspection = bundle.grounding_inspection
    if inspection is not None:
        return grounding_inspection_to_aspic(
            inspection,
            superiority=_source_superiority(bundle),
        )
    if not bundle.source_rules and not bundle.source_facts:
        return _empty_grounded_theory()
    raise ValueError(
        "GroundedRulesBundle must carry Gunray grounding_inspection for ASPIC projection"
    )


def _empty_grounded_theory() -> GroundedDatalogTheory:
    return GroundedDatalogTheory(
        system=ArgumentationSystem(
            language=frozenset(),
            contrariness=ContrarinessFn(
                contradictories=frozenset(),
                contraries=frozenset(),
            ),
            strict_rules=frozenset(),
            defeasible_rules=frozenset(),
        ),
        kb=KnowledgeBase(axioms=frozenset(), premises=frozenset()),
        pref=PreferenceConfig(
            rule_order=frozenset(),
            premise_order=frozenset(),
            comparison="elitist",
            link="last",
        ),
        inspection=None,  # type: ignore[arg-type]
        source_to_ground_rules={},
        rule_origins={},
        non_approximated_predicates=frozenset(),
    )


def _extend_literals(
    literals: dict[LiteralKey, Literal],
    rules: frozenset[Rule],
    axioms: frozenset[Literal],
) -> dict[LiteralKey, Literal]:
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
    complement_encoder: ComplementEncoder,
) -> GroundedAspicProjection:
    """Translate a grounded Gunray bundle into ASPIC+ rules.

    The projection lives in ``argumentation.datalog_grounding``; propstore only
    supplies its existing bundle envelope and keeps the literal-key dictionary
    current for downstream projection code.
    """

    del complement_encoder
    grounded = _project_bundle(bundle)
    strict_rules = grounded.system.strict_rules
    defeasible_rules = grounded.system.defeasible_rules
    all_rules = strict_rules | defeasible_rules
    return GroundedAspicProjection(
        strict_rules=strict_rules,
        defeasible_rules=defeasible_rules,
        literals=_extend_literals(literals, all_rules, grounded.kb.axioms),
        origins=grounded.rule_origins,
        rule_order=grounded.pref.rule_order,
    )


def _ground_facts_to_axioms(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    kb: KnowledgeBase,
    *,
    complement_encoder: ComplementEncoder,
) -> KnowledgeBase:
    """Inject grounded Gunray facts into ``K_n``."""

    del complement_encoder
    grounded = _project_bundle(bundle)
    _extend_literals(literals, frozenset(), grounded.kb.axioms)
    return KnowledgeBase(
        axioms=kb.axioms | grounded.kb.axioms,
        premises=kb.premises,
    )


__all__ = [
    "GroundedAspicProjection",
    "project_grounded_rules",
]
