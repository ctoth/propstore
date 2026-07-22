"""Behavioral subset of the grounding inspection/read surface."""

from __future__ import annotations

import gunray
import pytest

from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.grounder import ground
from propstore.grounding.inspection import (
    format_argument,
    format_ground_atom,
    format_ground_rule,
    parse_query_atom,
)
from propstore.grounding.predicates import PredicateRegistry


def _registry() -> PredicateRegistry:
    return PredicateRegistry.from_documents(())


def test_parse_query_atom_round_trips() -> None:
    parsed = parse_query_atom('bird("tweety")')
    assert parsed.predicate == "bird"


def test_parse_query_atom_rejects_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        parse_query_atom("   ")


def test_format_ground_atom() -> None:
    assert (
        format_ground_atom(gunray.GroundAtom(predicate="rains", arguments=()))
        == "rains"
    )
    assert (
        format_ground_atom(gunray.GroundAtom(predicate="bird", arguments=("tweety",)))
        == "bird(tweety)"
    )


def test_format_ground_rule() -> None:
    theory = gunray.DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=(gunray.Rule(id="s1", head="animal(X)", body=("bird(X)",)),),
    )
    instance = next(iter(gunray.inspect_grounding(theory).all_rule_instances))
    rendered = format_ground_rule(instance)
    assert rendered.startswith("s1:")
    assert "<-" in rendered


def test_format_argument() -> None:
    rules = (
        DefeasibleRule(
            rule_id="s1",
            kind="strict",
            head=Atom(predicate="animal", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(predicate="bird", terms=(Term(kind="var", name="X"),)),
                ),
            ),
        ),
    )
    facts = (gunray.GroundAtom(predicate="bird", arguments=("tweety",)),)
    bundle = ground(rules, facts, _registry())
    rendered = {format_argument(argument) for argument in bundle.arguments}
    assert any("|-" in line for line in rendered)
