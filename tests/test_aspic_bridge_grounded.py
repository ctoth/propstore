"""Gunray grounding-inspection → ASPIC+ projection seam (Phase 6b).

Pins the contract for ``propstore.aspic_bridge.project_grounded_rules`` over a
*non-empty* grounded bundle: it must hand the bundle's ``gunray.GroundingInspection``
to the argumentation package's ``grounding_inspection_to_aspic`` and surface the
resulting strict/defeasible rules, rule origins, superiority order, and the
extended literal dictionary.

Behavioral contract is ported from the pre-rewrite
``tests/test_aspic_bridge_grounded.py``; the rule-construction helpers are
re-expressed over the rewrite's ``DefeasibleRule`` / ``grounder.ground`` surface
(the pre-rewrite ``RuleDocument`` document family does not exist in the rewrite).

Garcia & Simari 2004 §3 (pp.3-4): the canonical ``flies(X) -< bird(X)`` defeasible
example; Herbrand grounding produces one rule instance per fact-base binding.
"""

from __future__ import annotations

import gunray
from argumentation.structured.aspic.aspic import GroundAtom, KnowledgeBase, Literal

from propstore.aspic_bridge import project_grounded_rules
from propstore.aspic_bridge.grounding import ground_facts_to_axioms
from propstore.core.literal_keys import LiteralKey, claim_key, ground_key
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import GroundedRulesBundle
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


def _ground(
    rules: tuple[DefeasibleRule, ...],
    facts: tuple[gunray.GroundAtom, ...],
) -> GroundedRulesBundle:
    return ground(rules, facts, _registry(), return_arguments=True)


def _fact(predicate: str, *constants: str) -> gunray.GroundAtom:
    return gunray.GroundAtom(predicate=predicate, arguments=constants)


def test_empty_canonical_bundle_projects_to_empty_rule_sets() -> None:
    projection = project_grounded_rules(GroundedRulesBundle.empty(), {})
    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()
    assert projection.literals == {}


def test_empty_grounded_program_projects_to_empty_rule_sets() -> None:
    projection = project_grounded_rules(_ground((), ()), {})
    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()
    assert projection.literals == {}


def test_single_defeasible_rule_with_one_fact_projects_one_instance() -> None:
    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("bird", "tweety"),))

    projection = project_grounded_rules(bundle, {})

    assert projection.strict_rules == frozenset()
    assert len(projection.defeasible_rules) == 1
    emitted = next(iter(projection.defeasible_rules))
    assert emitted.kind == "defeasible"
    assert emitted.consequent == Literal(
        atom=GroundAtom("flies", ("tweety",)), negated=False
    )
    assert emitted.antecedents == (
        Literal(atom=GroundAtom("bird", ("tweety",)), negated=False),
    )
    assert projection.origins[emitted].source_rule_id == "rule:birds-fly"


def test_two_matching_facts_project_two_instances() -> None:
    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("bird", "tweety"), _fact("bird", "opus")))

    projection = project_grounded_rules(bundle, {})

    assert len(projection.defeasible_rules) == 2
    consequents = {
        rule.consequent.atom.arguments for rule in projection.defeasible_rules
    }
    assert consequents == {("tweety",), ("opus",)}
    names = {rule.name for rule in projection.defeasible_rules}
    assert len(names) == 2


def test_rule_with_no_matching_fact_projects_zero_instances() -> None:
    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("mammal", "fido"),))

    projection = project_grounded_rules(bundle, {})

    assert projection.strict_rules == frozenset()
    assert projection.defeasible_rules == frozenset()


def test_multi_body_rule_requires_joint_substitution() -> None:
    rule = DefeasibleRule(
        rule_id="rule:feathered-birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"), _pos("feathered", "X")),
    )
    bundle = _ground(
        (rule,),
        (_fact("bird", "tweety"), _fact("bird", "opus"), _fact("feathered", "tweety")),
    )

    projection = project_grounded_rules(bundle, {})

    assert len(projection.defeasible_rules) == 1
    emitted = next(iter(projection.defeasible_rules))
    assert emitted.consequent.atom.arguments == ("tweety",)
    assert tuple(a.atom.predicate for a in emitted.antecedents) == ("bird", "feathered")


def test_existing_literals_preserved_and_grounded_atoms_added() -> None:
    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("bird", "tweety"),))

    seed_key = claim_key("claim-alpha")
    seed_lit = Literal(atom=GroundAtom("claim-alpha"), negated=False)
    literals: dict[LiteralKey, Literal] = {seed_key: seed_lit}

    out = project_grounded_rules(bundle, literals).literals

    assert out[seed_key] == seed_lit
    assert ground_key(GroundAtom("flies", ("tweety",)), False) in out
    assert ground_key(GroundAtom("bird", ("tweety",)), False) in out


def test_grounded_literals_satisfy_contrary_involution() -> None:
    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("bird", "tweety"),))

    projection = project_grounded_rules(bundle, {})

    for rule_obj in projection.defeasible_rules:
        assert rule_obj.consequent.contrary.contrary == rule_obj.consequent
        for ante in rule_obj.antecedents:
            assert ante.contrary.contrary == ante


def test_strict_fact_rule_folds_into_axioms() -> None:
    rule = DefeasibleRule(
        rule_id="rule:hard-birds-fly",
        kind="strict",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = _ground((rule,), (_fact("bird", "tweety"),))

    projection = project_grounded_rules(bundle, {})
    assert projection.defeasible_rules == frozenset()

    kb = ground_facts_to_axioms(
        bundle,
        {},
        KnowledgeBase(axioms=frozenset(), premises=frozenset()),
    )
    assert Literal(GroundAtom("flies", ("tweety",))) in kb.axioms


def test_non_empty_bundle_without_inspection_is_rejected() -> None:
    import pytest

    rule = DefeasibleRule(
        rule_id="rule:birds-fly",
        kind="defeasible",
        head=_atom("flies", "X"),
        body=(_pos("bird", "X"),),
    )
    bundle = GroundedRulesBundle(
        source_rules=(rule,),
        source_facts=(),
        sections=GroundedRulesBundle.empty().sections,
    )
    with pytest.raises(ValueError, match="grounding_inspection"):
        project_grounded_rules(bundle, {})
