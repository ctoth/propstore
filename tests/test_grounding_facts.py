"""Fact extraction from the concept/claim substrate per derived_from specs."""

from __future__ import annotations

import gunray
import pytest

from propstore.families.claims import Claim
from propstore.families.predicates import Predicate
from propstore.grounding.facts import ConceptRelations, GroundingFactInputs, extract_facts
from propstore.grounding.predicates import PredicateArityMismatchError, PredicateRegistry


def _registry(*predicates: Predicate) -> PredicateRegistry:
    return PredicateRegistry.from_documents(predicates)


def _atoms(
    facts: tuple[gunray.GroundAtom, ...],
) -> set[tuple[str, tuple[gunray.Scalar, ...]]]:
    return {(fact.predicate, fact.arguments) for fact in facts}


def test_concept_relation_emits_unary_fact() -> None:
    registry = _registry(
        Predicate(
            predicate_id="bird",
            arity=1,
            arg_types=("Concept",),
            derived_from="concept.relation:is_a:Bird",
        )
    )
    concepts = (
        ConceptRelations(concept_id="c1", canonical_name="tweety", relationships=(("is_a", "Bird"),)),
        ConceptRelations(concept_id="c2", canonical_name="rex", relationships=(("is_a", "Dog"),)),
    )
    facts = extract_facts(GroundingFactInputs(concepts=concepts), registry)
    assert _atoms(facts) == {("bird", ("tweety",))}


def test_concept_relation_rejects_non_unary_predicate() -> None:
    registry = _registry(
        Predicate(
            predicate_id="bird",
            arity=2,
            arg_types=("Concept", "Concept"),
            derived_from="concept.relation:is_a:Bird",
        )
    )
    concepts = (ConceptRelations(concept_id="c1", canonical_name="tweety", relationships=(("is_a", "Bird"),)),)
    with pytest.raises(PredicateArityMismatchError):
        extract_facts(GroundingFactInputs(concepts=concepts), registry)


def test_claim_role_about_output_target() -> None:
    registry = _registry(
        Predicate(predicate_id="about", arity=2, arg_types=("Claim", "Concept"), derived_from="claim.role:about"),
        Predicate(predicate_id="outputs", arity=2, arg_types=("Claim", "Concept"), derived_from="claim.role:output"),
        Predicate(predicate_id="targets", arity=2, arg_types=("Claim", "Concept"), derived_from="claim.role:target"),
    )
    claim = Claim(
        claim_id="cl1",
        concepts=("a1", "a2"),
        output_concept="o1",
        target_concept="t1",
    )
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert _atoms(facts) == {
        ("about", ("cl1", "a1")),
        ("about", ("cl1", "a2")),
        ("outputs", ("cl1", "o1")),
        ("targets", ("cl1", "t1")),
    }


def test_claim_context_fact() -> None:
    registry = _registry(
        Predicate(predicate_id="in_ctx", arity=2, arg_types=("Claim", "Context"), derived_from="claim.context")
    )
    claim = Claim(claim_id="cl1", context_id="ctx1")
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert _atoms(facts) == {("in_ctx", ("cl1", "ctx1"))}


def test_claim_attribute_arity1_and_arity2() -> None:
    registry = _registry(
        Predicate(predicate_id="has_conf", arity=1, arg_types=("Claim",), derived_from="claim.attribute:confidence"),
        Predicate(
            predicate_id="conf_val",
            arity=2,
            arg_types=("Claim", "Scalar"),
            derived_from="claim.attribute:confidence",
        ),
    )
    claim = Claim(claim_id="cl1", confidence=0.9)
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert _atoms(facts) == {("has_conf", ("cl1",)), ("conf_val", ("cl1", 0.9))}


def test_claim_attribute_absent_contributes_nothing() -> None:
    registry = _registry(
        Predicate(predicate_id="has_conf", arity=1, arg_types=("Claim",), derived_from="claim.attribute:confidence")
    )
    claim = Claim(claim_id="cl1")
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert facts == ()


def test_claim_condition_matches_authored_condition() -> None:
    registry = _registry(
        Predicate(predicate_id="cond", arity=1, arg_types=("Claim",), derived_from="claim.condition:t>0")
    )
    claim = Claim(claim_id="cl1", conditions=("t>0", "p<1"))
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert _atoms(facts) == {("cond", ("cl1",))}


def test_claim_provenance_reads_named_field() -> None:
    registry = _registry(
        Predicate(
            predicate_id="prov",
            arity=2,
            arg_types=("Claim", "Scalar"),
            derived_from="claim.provenance:uncertainty_type",
        )
    )
    claim = Claim(claim_id="cl1", uncertainty_type="stddev")
    facts = extract_facts(GroundingFactInputs(claims=(claim,)), registry)
    assert _atoms(facts) == {("prov", ("cl1", "stddev"))}


def test_derived_from_none_contributes_nothing() -> None:
    registry = _registry(Predicate(predicate_id="bare", arity=1, arg_types=("Concept",)))
    concepts = (ConceptRelations(concept_id="c1", canonical_name="x", relationships=(("is_a", "Bird"),)),)
    facts = extract_facts(GroundingFactInputs(concepts=concepts), registry)
    assert facts == ()


def test_facts_are_deduplicated_and_sorted() -> None:
    registry = _registry(
        Predicate(predicate_id="about", arity=2, arg_types=("Claim", "Concept"), derived_from="claim.role:about")
    )
    # Two claims, overlapping + distinct concepts; output must be sorted + unique.
    claims = (
        Claim(claim_id="c2", concepts=("z", "a")),
        Claim(claim_id="c1", concepts=("a",)),
    )
    facts = extract_facts(GroundingFactInputs(claims=claims), registry)
    rendered = [(f.predicate, f.arguments) for f in facts]
    assert rendered == sorted(rendered)
    assert len(set(rendered)) == len(rendered)
