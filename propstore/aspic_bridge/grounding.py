"""Grounded-rule translation and fact injection for the ASPIC bridge."""

from __future__ import annotations

import json
from collections.abc import Iterator

from propstore.families.documents.rules import AtomDocument
from argumentation.aspic import GroundAtom, KnowledgeBase, Literal, Rule, Scalar
from propstore.core.literal_keys import LiteralKey, ground_key
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.complement import ComplementEncoder
from argumentation.preference import strict_partial_order_closure

_GroundFactKey = tuple[str, bool]


def _decode_grounded_predicate(
    predicate_id: str,
    complement_encoder: ComplementEncoder,
) -> _GroundFactKey:
    """Decode the grounded predicate convention into typed polarity."""

    toggled = complement_encoder.complement(predicate_id)
    negated = len(toggled) < len(predicate_id)
    positive = toggled if negated else predicate_id
    return positive, negated


def _try_match(
    atom: AtomDocument,
    fact_args: tuple[Scalar, ...],
    sigma: dict[str, Scalar],
) -> dict[str, Scalar] | None:
    """Try to unify one rule-body atom against one grounded fact."""

    if len(atom.terms) != len(fact_args):
        return None
    extended = dict(sigma)
    for term, fact_arg in zip(atom.terms, fact_args):
        if term.kind == "var":
            name = term.name
            if name is None:
                return None
            if name in extended:
                if extended[name] != fact_arg:
                    return None
            else:
                extended[name] = fact_arg
        elif term.kind == "const":
            if term.value != fact_arg:
                return None
        else:
            return None
    return extended


def _enumerate_substitutions(
    body_atoms: tuple[AtomDocument, ...],
    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]],
) -> Iterator[dict[str, Scalar]]:
    """Yield every consistent substitution grounding all rule-body atoms."""

    partial_subs: list[dict[str, Scalar]] = [{}]
    for atom in body_atoms:
        next_subs: list[dict[str, Scalar]] = []
        for sigma in partial_subs:
            for fact_args in facts.get((atom.predicate, atom.negated), set()):
                extended = _try_match(atom, fact_args, sigma)
                if extended is not None:
                    next_subs.append(extended)
        partial_subs = next_subs
        if not partial_subs:
            break
    return iter(partial_subs)


def _apply_substitution(
    atom: AtomDocument,
    sigma: dict[str, Scalar],
) -> GroundAtom:
    """Apply a grounding substitution to one schema atom."""

    args: list[Scalar] = []
    for term in atom.terms:
        if term.kind == "var":
            name = term.name
            if name is None or name not in sigma:
                raise ValueError(
                    f"Unsafe rule: variable {name!r} in atom {atom.predicate!r} "
                    "not bound by substitution"
                )
            args.append(sigma[name])
        elif term.kind == "const":
            if term.value is None:
                raise ValueError(
                    f"Constant term in atom {atom.predicate!r} has no value"
                )
            args.append(term.value)
        else:
            raise ValueError(
                f"Unknown term kind {term.kind!r} in atom {atom.predicate!r}"
            )
    return GroundAtom(predicate=atom.predicate, arguments=tuple(args))


def _typed_scalar_key(value: Scalar) -> dict[str, Scalar | str]:
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": value}


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


def _canonical_substitution_key(sigma: dict[str, Scalar]) -> str:
    """Render a substitution as a stable structured string."""

    return json.dumps(
        {name: _typed_scalar_key(sigma[name]) for name in sorted(sigma)},
        sort_keys=True,
        separators=(",", ":"),
    )


def grounded_rules_to_rules(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    *,
    complement_encoder: ComplementEncoder,
) -> tuple[frozenset[Rule], frozenset[Rule], dict[LiteralKey, Literal]]:
    """Translate grounded gunray rules into ASPIC+ rules."""

    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]] = {}
    for section_name in ("definitely", "defeasibly"):
        section = bundle.sections.get(section_name, {})
        for predicate_id, rows in section.items():
            bucket = facts.setdefault(
                _decode_grounded_predicate(predicate_id, complement_encoder),
                set(),
            )
            for row in rows:
                bucket.add(row)

    strict_rules: list[Rule] = []
    defeasible_rules: list[Rule] = []
    pending_defeaters: list[tuple[tuple[Literal, ...], Literal, str]] = []

    for rule_file in bundle.source_rules:
        for rule_doc in rule_file.document.rules:
            for sigma in _enumerate_substitutions(rule_doc.body, facts):
                antecedent_literals: list[Literal] = []
                for body_atom in rule_doc.body:
                    ground = _apply_substitution(body_atom, sigma)
                    antecedent_literals.append(
                        _literal_for_atom(ground, body_atom.negated, literals)
                    )

                head_ground = _apply_substitution(rule_doc.head, sigma)
                consequent = _literal_for_atom(
                    head_ground,
                    rule_doc.head.negated,
                    literals,
                )
                rule_name = f"{rule_doc.id}#{_canonical_substitution_key(sigma)}"
                antecedents = tuple(antecedent_literals)
                if rule_doc.kind == "strict":
                    strict_rules.append(
                        Rule(
                            antecedents=antecedents,
                            consequent=consequent,
                            kind="strict",
                            name=None,
                        )
                    )
                    continue
                if rule_doc.kind == "defeasible":
                    defeasible_rules.append(
                        Rule(
                            antecedents=antecedents,
                            consequent=consequent,
                            kind="defeasible",
                            name=rule_name,
                        )
                    )
                    continue
                pending_defeaters.append((antecedents, consequent, rule_name))

    grounded_defeaters: list[Rule] = []
    for antecedents, defeater_head, defeater_name in pending_defeaters:
        opposing_rules = [
            rule
            for rule in defeasible_rules
            if rule.name is not None and rule.consequent == defeater_head.contrary
        ]
        for target_rule in opposing_rules:
            assert target_rule.name is not None
            undercut_literal = _literal_for_atom(
                GroundAtom(target_rule.name),
                True,
                literals,
            )
            grounded_defeaters.append(
                Rule(
                    antecedents=antecedents,
                    consequent=undercut_literal,
                    kind="defeasible",
                    name=f"{defeater_name}->{target_rule.name}",
                )
            )

    defeasible_rules.extend(grounded_defeaters)
    return frozenset(strict_rules), frozenset(defeasible_rules), literals


def grounded_rule_order_from_bundle(
    bundle: GroundedRulesBundle,
    defeasible_rules: frozenset[Rule],
) -> frozenset[tuple[Rule, Rule]]:
    """Project authored superiority onto grounded ASPIC+ rule objects.

    Rule files author Garcia-Simari superiority as
    ``(superior_rule_id, inferior_rule_id)``. ASPIC+ preference config
    stores ``(weaker_rule, stronger_rule)`` pairs. A schematic superiority
    pair applies to every grounded instance whose rule name begins with the
    authored rule id.
    """

    authored_pairs = [
        pair
        for rule_file in bundle.source_rules
        for pair in rule_file.document.superiority
    ]
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
        if not stronger_rules or not weaker_rules:
            continue
        for weaker in weaker_rules:
            for stronger in stronger_rules:
                if weaker != stronger:
                    projected.add((weaker, stronger))

    return strict_partial_order_closure(projected)


def _source_rule_id(rule_name: str) -> str:
    """Return the authored rule id prefix from a grounded ASPIC rule name."""

    return rule_name.split("#", 1)[0]


def _ground_facts_to_axioms(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    kb: KnowledgeBase,
    *,
    complement_encoder: ComplementEncoder,
) -> KnowledgeBase:
    """Inject bundle ``definitely`` facts into ``K_n``."""

    axioms: set[Literal] = set(kb.axioms)
    definitely = bundle.sections.get("definitely", {})
    for predicate_id, rows in definitely.items():
        predicate, negated = _decode_grounded_predicate(predicate_id, complement_encoder)
        for row in rows:
            ground = GroundAtom(predicate=predicate, arguments=tuple(row))
            axioms.add(_literal_for_atom(ground, negated, literals))

    return KnowledgeBase(axioms=frozenset(axioms), premises=kb.premises)


__all__ = [
    "grounded_rule_order_from_bundle",
    "grounded_rules_to_rules",
]
