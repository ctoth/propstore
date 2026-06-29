"""`ground` returns enumerated arguments by default."""

from __future__ import annotations

import gunray

from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry


def _program() -> tuple[tuple[DefeasibleRule, ...], tuple[gunray.GroundAtom, ...]]:
    rules = (
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="flies", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(predicate="bird", terms=(Term(kind="var", name="X"),)),
                ),
            ),
        ),
    )
    facts = (gunray.GroundAtom(predicate="bird", arguments=("tweety",)),)
    return rules, facts


def test_ground_returns_arguments_by_default() -> None:
    rules, facts = _program()
    bundle = ground(rules, facts, PredicateRegistry.from_documents(()))
    assert bundle.status == "complete"
    assert len(bundle.arguments) > 0


def test_ground_suppresses_arguments_when_requested() -> None:
    rules, facts = _program()
    bundle = ground(
        rules, facts, PredicateRegistry.from_documents(()), return_arguments=False
    )
    assert bundle.arguments == ()
