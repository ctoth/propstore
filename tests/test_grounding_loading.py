"""Assembling a grounded bundle from the authored substrate."""

from __future__ import annotations

import pytest

from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import SECTION_NAMES
from propstore.grounding.facts import ConceptRelations
from propstore.grounding.loading import GroundingRepo, build_grounded_bundle


def test_empty_surface_yields_empty_bundle() -> None:
    bundle = build_grounded_bundle(GroundingRepo())
    assert bundle.status == "complete"
    assert set(bundle.sections.keys()) == set(SECTION_NAMES)
    assert all(bundle.sections[name] == {} for name in SECTION_NAMES)


def test_rules_without_predicates_is_invalid_surface() -> None:
    rule = DefeasibleRule(
        rule_id="r1",
        kind="defeasible",
        head=Atom(predicate="h", terms=(Term(kind="var", name="X"),)),
    )
    with pytest.raises(ValueError, match="rules/") as excinfo:
        build_grounded_bundle(GroundingRepo(rules=(rule,)))
    assert "predicates/" in str(excinfo.value)


def test_full_build_grounds_facts_from_concepts() -> None:
    repo = GroundingRepo(
        predicates=(
            Predicate(
                predicate_id="bird",
                arity=1,
                arg_types=("Concept",),
                derived_from="concept.relation:is_a:Bird",
            ),
        ),
        rules=(
            DefeasibleRule(
                rule_id="r1",
                kind="defeasible",
                head=Atom(predicate="flies", terms=(Term(kind="var", name="X"),)),
                body=(
                    BodyLiteral(
                        kind="positive",
                        atom=Atom(
                            predicate="bird", terms=(Term(kind="var", name="X"),)
                        ),
                    ),
                ),
            ),
        ),
        concepts=(
            ConceptRelations(
                concept_id="c1",
                canonical_name="tweety",
                relationships=(("is_a", "Bird"),),
            ),
        ),
    )
    bundle = build_grounded_bundle(repo, return_arguments=True)
    assert ("tweety",) in bundle.sections["yes"]["bird"]
    assert ("tweety",) in bundle.sections["yes"]["flies"]
    assert len(bundle.arguments) > 0
