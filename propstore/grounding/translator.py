"""Lower authored DeLP rules + ground facts into a :class:`gunray.DefeasibleTheory`.

This is the grounding boundary: structured :class:`~propstore.families.rules.DefeasibleRule`
documents and :class:`gunray.GroundAtom` facts are compiled to gunray's surface
syntax (``gunray.Rule`` string heads/bodies and a predicate-keyed fact dict),
then handed to ``gunray.DefeasibleTheory``. Crossing the boundary is a CALL that
returns gunray's own type — there is no propstore mirror of the theory.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

import gunray
from argumentation.core.preference import strict_partial_order_closure

from propstore.families.rules import (
    Atom,
    BodyLiteral,
    DefeasibleRule,
    RuleSuperiority,
    Term,
)
from propstore.grounding.predicates import PredicateRegistry


def translate_to_theory(
    rules: Sequence[DefeasibleRule],
    facts: tuple[gunray.GroundAtom, ...],
    registry: PredicateRegistry,
    *,
    superiority: Sequence[RuleSuperiority] = (),
) -> gunray.DefeasibleTheory:
    """Compile authored rules + facts into a gunray defeasible theory.

    ``strict`` rules route to ``strict_rules``, ``defeasible`` to
    ``defeasible_rules``, and both defeater kinds collapse to gunray's single
    ``defeaters`` slot. ``registry`` is threaded for symmetry with the wider
    grounding pipeline; argument-type validation already happened at fact
    extraction.
    """

    _ = registry
    strict_rules: list[gunray.Rule] = []
    defeasible_rules: list[gunray.Rule] = []
    defeaters: list[gunray.Rule] = []
    non_strict_rule_ids: set[str] = set()
    for rule in rules:
        gunray_rule = gunray.Rule(
            id=rule.rule_id,
            head=_stringify_atom(rule.head),
            body=tuple(_stringify_body_literal(literal) for literal in rule.body),
        )
        if rule.kind == "strict":
            strict_rules.append(gunray_rule)
        elif rule.kind == "defeasible":
            defeasible_rules.append(gunray_rule)
            non_strict_rule_ids.add(rule.rule_id)
        else:  # proper_defeater or blocking_defeater both lower to gunray defeaters
            defeaters.append(gunray_rule)
            non_strict_rule_ids.add(rule.rule_id)

    grouped_facts: dict[str, list[tuple[gunray.Scalar, ...]]] = {}
    for fact in facts:
        grouped_facts.setdefault(fact.predicate, []).append(tuple(fact.arguments))

    return gunray.DefeasibleTheory(
        facts=grouped_facts,
        strict_rules=tuple(strict_rules),
        defeasible_rules=tuple(defeasible_rules),
        defeaters=tuple(defeaters),
        superiority=_normalise_superiority(superiority, non_strict_rule_ids),
        conflicts=(),
    )


def _stringify_atom(atom: Atom) -> str:
    predicate = f"~{atom.predicate}" if atom.negated else atom.predicate
    if not atom.terms:
        return predicate
    rendered = ", ".join(_stringify_term(term) for term in atom.terms)
    return f"{predicate}({rendered})"


def _stringify_body_literal(literal: BodyLiteral) -> str:
    atom_text = _stringify_atom(literal.atom)
    if literal.kind == "positive":
        return atom_text
    return f"not {atom_text}"


def _stringify_term(term: Term) -> str:
    if term.kind == "var":
        if term.name is None:
            raise ValueError("variable Term is missing its 'name' field")
        return term.name
    value = term.value
    if value is None:
        raise ValueError("constant Term is missing its 'value' field")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    return json.dumps(value)


def _normalise_superiority(
    superiority: Sequence[RuleSuperiority], non_strict_rule_ids: set[str]
) -> tuple[tuple[str, str], ...]:
    """Validate, orient, and transitively close authored superiorities.

    Authored pairs are ``(superior, inferior)``. The closure helper works over
    ``(weaker, stronger)`` pairs, so we invert in and back out, returning oriented
    ``(superior, inferior)`` tuples in deterministic order.
    """

    if not superiority:
        return ()
    authored_pairs = [
        (item.superior_rule_id, item.inferior_rule_id) for item in superiority
    ]
    referenced = {rule_id for pair in authored_pairs for rule_id in pair}
    missing = referenced - non_strict_rule_ids
    if missing:
        raise ValueError(
            "superiority references unknown or strict rule id(s): "
            + ", ".join(sorted(missing))
        )
    closed = strict_partial_order_closure(
        (inferior, superior) for superior, inferior in authored_pairs
    )
    return tuple(
        (stronger, weaker)
        for weaker, stronger in sorted(
            closed, key=lambda pair: (str(pair[1]), str(pair[0]))
        )
    )
