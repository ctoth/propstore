"""Grounded-rule projection for the ASPIC bridge."""

from __future__ import annotations

import json
from collections.abc import Mapping

from argumentation.aspic import GroundAtom, KnowledgeBase, Literal, Rule
from argumentation.datalog_grounding import (
    GroundedDatalogTheory,
    ground_defeasible_theory,
    grounding_inspection_to_aspic,
)
from argumentation.preference import strict_partial_order_closure
from propstore.core.literal_keys import LiteralKey, ground_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.complement import ComplementEncoder
from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import translate_to_theory

_GroundFactKey = tuple[str, bool]


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
        pair
        for rule_file in bundle.source_rules
        for pair in rule_file.document.superiority
    )


def _project_bundle(bundle: GroundedRulesBundle) -> GroundedDatalogTheory:
    inspection = bundle.grounding_inspection
    if inspection is not None:
        return grounding_inspection_to_aspic(
            inspection,
            superiority=_source_superiority(bundle),
        )

    theory = translate_to_theory(
        bundle.source_rules,
        _fallback_facts(bundle),
        PredicateRegistry(()),
    )
    return ground_defeasible_theory(theory)


def _fallback_facts(bundle: GroundedRulesBundle) -> tuple[GroundAtom, ...]:
    facts: set[GroundAtom] = set(bundle.source_facts)
    for predicate_id, rows in bundle.sections.get("yes", {}).items():
        for row in rows:
            facts.add(GroundAtom(predicate_id, tuple(row)))
    return tuple(sorted(facts, key=lambda atom: (atom.predicate, atom.arguments)))


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


def grounded_rules_to_rules(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    *,
    complement_encoder: ComplementEncoder,
) -> tuple[frozenset[Rule], frozenset[Rule], dict[LiteralKey, Literal]]:
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
    return (
        strict_rules,
        defeasible_rules,
        _extend_literals(literals, all_rules, grounded.kb.axioms),
    )


def grounded_rule_order_from_bundle(
    bundle: GroundedRulesBundle,
    defeasible_rules: frozenset[Rule],
) -> frozenset[tuple[Rule, Rule]]:
    """Project authored superiority onto grounded ASPIC+ rule objects."""

    authored_pairs = _source_superiority(bundle)
    if not authored_pairs:
        return frozenset()

    by_source_id: dict[str, list[Rule]] = {}
    for rule in defeasible_rules:
        if rule.name is None:
            continue
        by_source_id.setdefault(_source_rule_id(rule.name), []).append(rule)

    projected: set[tuple[Rule, Rule]] = set()
    for superior_id, inferior_id in authored_pairs:
        stronger_rules = by_source_id.get(superior_id, [])
        weaker_rules = by_source_id.get(inferior_id, [])
        for weaker in weaker_rules:
            for stronger in stronger_rules:
                if weaker != stronger:
                    projected.add((weaker, stronger))

    return strict_partial_order_closure(projected)


def _source_rule_id(rule_name: str) -> str:
    return rule_name.split("#", 1)[0]


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
    "grounded_rule_order_from_bundle",
    "grounded_rules_to_rules",
]
