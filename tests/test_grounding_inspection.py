"""Behavioral subset of the grounding inspection/read surface."""

from __future__ import annotations

import gunray
import pytest

from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.grounder import ground
from propstore.grounding.inspection import (
    format_argument,
    format_ground_atom,
    format_ground_rule,
    grounding_surface_state,
    parse_query_atom,
)
from propstore.grounding.loading import GroundingRepo
from propstore.grounding.predicates import PredicateRegistry


def _registry() -> PredicateRegistry:
    return PredicateRegistry.from_documents(())


def test_surface_state_none() -> None:
    assert grounding_surface_state(GroundingRepo()) == "none"


def test_surface_state_invalid() -> None:
    rule = DefeasibleRule(
        rule_id="r1",
        kind="defeasible",
        head=Atom(predicate="h", terms=(Term(kind="var", name="X"),)),
    )
    assert grounding_surface_state(GroundingRepo(rules=(rule,))) == "invalid"


def test_surface_state_ready() -> None:
    predicate = Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    assert grounding_surface_state(GroundingRepo(predicates=(predicate,))) == "ready"


def test_parse_query_atom_round_trips() -> None:
    parsed = parse_query_atom('bird("tweety")')
    assert parsed.predicate == "bird"


def test_parse_query_atom_rejects_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        parse_query_atom("   ")


def test_format_ground_atom() -> None:
    assert format_ground_atom(gunray.GroundAtom(predicate="rains", arguments=())) == "rains"
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
