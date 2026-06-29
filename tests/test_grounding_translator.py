"""Lowering authored rules + facts into a gunray.DefeasibleTheory."""

from __future__ import annotations

import gunray

from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, RuleSuperiority, Term
from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import (
    _stringify_atom,
    _stringify_body_literal,
    translate_to_theory,
)


def _var(name: str) -> Term:
    return Term(kind="var", name=name)


def _const(value: str | int | float | bool) -> Term:
    return Term(kind="const", value=value)


def _registry() -> PredicateRegistry:
    return PredicateRegistry.from_documents(())


def test_stringify_arity0_is_bare_predicate() -> None:
    assert _stringify_atom(Atom(predicate="rains")) == "rains"


def test_stringify_strong_negation_prefix() -> None:
    assert _stringify_atom(Atom(predicate="flies", terms=(_var("X"),), negated=True)) == "~flies(X)"


def test_stringify_default_negation_prefix() -> None:
    literal = BodyLiteral(kind="default_negated", atom=Atom(predicate="ab", terms=(_var("X"),)))
    assert _stringify_body_literal(literal) == "not ab(X)"


def test_stringify_term_kinds() -> None:
    assert _stringify_atom(Atom(predicate="p", terms=(_const(True), _const(False)))) == "p(true, false)"
    assert _stringify_atom(Atom(predicate="p", terms=(_const(42),))) == "p(42)"
    assert _stringify_atom(Atom(predicate="p", terms=(_const(1.5),))) == "p(1.5)"
    assert _stringify_atom(Atom(predicate="p", terms=(_const("tweety"),))) == 'p("tweety")'


def test_stringified_atoms_round_trip_through_gunray_parser() -> None:
    atoms = [
        Atom(predicate="flag"),
        Atom(predicate="bird", terms=(_const("tweety"),)),
        Atom(predicate="pair", terms=(_const(42), _const(True))),
        Atom(predicate="quoted", terms=(_const('line1\nline2\t"q"'),)),
    ]
    for atom in atoms:
        text = _stringify_atom(atom)
        parsed = gunray.parse_atom_text(text)
        assert parsed.predicate == atom.predicate
        assert len(parsed.terms) == len(atom.terms)


def test_rule_kinds_route_to_theory_slots() -> None:
    head = Atom(predicate="h", terms=(_var("X"),))
    body = (BodyLiteral(kind="positive", atom=Atom(predicate="b", terms=(_var("X"),))),)
    rules = (
        DefeasibleRule(rule_id="s1", kind="strict", head=head, body=body),
        DefeasibleRule(rule_id="d1", kind="defeasible", head=head, body=body),
        DefeasibleRule(rule_id="p1", kind="proper_defeater", head=head, body=body),
        DefeasibleRule(rule_id="b1", kind="blocking_defeater", head=head, body=body),
    )
    theory = translate_to_theory(rules, (), _registry())
    assert {rule.id for rule in theory.strict_rules} == {"s1"}
    assert {rule.id for rule in theory.defeasible_rules} == {"d1"}
    assert {rule.id for rule in theory.defeaters} == {"p1", "b1"}


def test_superiority_is_transitively_closed_and_oriented() -> None:
    head = Atom(predicate="h", terms=(_var("X"),))
    body = (BodyLiteral(kind="positive", atom=Atom(predicate="b", terms=(_var("X"),))),)
    rules = tuple(
        DefeasibleRule(rule_id=rid, kind="defeasible", head=head, body=body)
        for rid in ("r1", "r2", "r3")
    )
    superiority = (
        RuleSuperiority(superiority_id="x", superior_rule_id="r1", inferior_rule_id="r2"),
        RuleSuperiority(superiority_id="y", superior_rule_id="r2", inferior_rule_id="r3"),
    )
    theory = translate_to_theory(rules, (), _registry(), superiority=superiority)
    assert set(theory.superiority) == {("r1", "r2"), ("r2", "r3"), ("r1", "r3")}


def test_facts_grouped_by_predicate() -> None:
    facts = (
        gunray.GroundAtom(predicate="bird", arguments=("tweety",)),
        gunray.GroundAtom(predicate="bird", arguments=("polly",)),
        gunray.GroundAtom(predicate="penguin", arguments=("pingu",)),
    )
    theory = translate_to_theory((), facts, _registry())
    assert set(theory.facts["bird"]) == {("tweety",), ("polly",)}
    assert set(theory.facts["penguin"]) == {("pingu",)}
