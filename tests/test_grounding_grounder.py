"""End-to-end grounding into a non-committal bundle + the double-count regression."""

from __future__ import annotations

import collections
import dataclasses

import gunray
import pytest

from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import SECTION_NAMES
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry


def _var(name: str) -> Term:
    return Term(kind="var", name=name)


def _atom(predicate: str, variable: str, *, negated: bool = False) -> Atom:
    return Atom(predicate=predicate, terms=(_var(variable),), negated=negated)


def _pos(predicate: str, variable: str) -> BodyLiteral:
    return BodyLiteral(kind="positive", atom=_atom(predicate, variable))


def _registry() -> PredicateRegistry:
    return PredicateRegistry.from_documents(())


def _bird_penguin_rules() -> tuple[DefeasibleRule, ...]:
    return (
        DefeasibleRule(
            rule_id="s1",
            kind="strict",
            head=_atom("animal", "X"),
            body=(_pos("bird", "X"),),
        ),
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=_atom("flies", "X"),
            body=(_pos("bird", "X"),),
        ),
        DefeasibleRule(
            rule_id="d1",
            kind="proper_defeater",
            head=_atom("flies", "X", negated=True),
            body=(_pos("penguin", "X"),),
        ),
    )


def _bird_penguin_facts() -> tuple[gunray.GroundAtom, ...]:
    return (
        gunray.GroundAtom(predicate="bird", arguments=("tweety",)),
        gunray.GroundAtom(predicate="penguin", arguments=("tweety",)),
    )


def test_empty_program_yields_four_empty_sections() -> None:
    bundle = ground((), (), _registry())
    assert set(bundle.sections.keys()) == set(SECTION_NAMES)
    assert all(bundle.sections[name] == {} for name in SECTION_NAMES)
    assert bundle.status == "complete"


def test_sections_always_carry_all_four_keys() -> None:
    bundle = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry())
    assert set(bundle.sections.keys()) == set(SECTION_NAMES)


def test_strict_consequence_lands_in_yes() -> None:
    bundle = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry())
    assert ("tweety",) in bundle.sections["yes"]["animal"]
    assert ("tweety",) in bundle.sections["yes"]["bird"]


def test_bundle_is_immutable() -> None:
    bundle = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry())
    with pytest.raises(TypeError):
        bundle.sections["yes"] = {}
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.status = "mutated"


def test_arguments_returned_by_default() -> None:
    bundle = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry())
    assert len(bundle.arguments) > 0


def test_arguments_suppressed_when_not_requested() -> None:
    bundle = ground(
        _bird_penguin_rules(),
        _bird_penguin_facts(),
        _registry(),
        return_arguments=False,
    )
    assert bundle.arguments == ()


def test_arguments_are_deterministically_ordered() -> None:
    first = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry()).arguments
    second = ground(_bird_penguin_rules(), _bird_penguin_facts(), _registry()).arguments
    assert [a.conclusion.predicate for a in first] == [
        a.conclusion.predicate for a in second
    ]


def test_grounding_inspection_rule_instances_counts_each_kind_once() -> None:
    """Regression: gunray's ``all_rule_instances`` flattens each kind exactly once.

    A theory with one strict, one defeasible, and one defeater rule — each
    grounding to exactly one instance — must report three instances total with one
    per kind. The buggy reference reconstruction sliced and re-added the per-kind
    tuples; this pins the canonical flatten instead.
    """

    theory = gunray.DefeasibleTheory(
        facts={"bird": {("tweety",)}, "penguin": {("tweety",)}},
        strict_rules=(gunray.Rule(id="s1", head="animal(X)", body=("bird(X)",)),),
        defeasible_rules=(gunray.Rule(id="r1", head="flies(X)", body=("bird(X)",)),),
        defeaters=(gunray.Rule(id="d1", head="~flies(X)", body=("penguin(X)",)),),
    )
    inspection = gunray.inspect_grounding(theory)
    instances = inspection.all_rule_instances
    assert len(instances) == 3
    assert collections.Counter(instance.kind for instance in instances) == {
        "strict": 1,
        "defeasible": 1,
        "defeater": 1,
    }
    assert len({(i.rule_id, i.kind) for i in instances}) == 3
