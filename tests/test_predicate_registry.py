"""Predicate registry + derived_from DSL behavioral contract."""

from __future__ import annotations

import pytest
from condition_ir import KindType

from propstore.families.predicates import Predicate
from propstore.grounding.predicates import (
    DerivedFromParseError,
    DuplicatePredicateError,
    PredicateArgKindError,
    PredicateArityMismatchError,
    PredicateAtom,
    PredicateNotRegisteredError,
    PredicateRegistry,
    parse_derived_from,
)


def _registry(*predicates: Predicate) -> PredicateRegistry:
    return PredicateRegistry.from_documents(predicates)


def test_from_documents_rejects_duplicate_id() -> None:
    with pytest.raises(DuplicatePredicateError):
        _registry(
            Predicate(predicate_id="bird", arity=1, arg_types=("Concept",)),
            Predicate(predicate_id="bird", arity=1, arg_types=("Concept",)),
        )


def test_lookup_unknown_raises() -> None:
    registry = _registry(
        Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    with pytest.raises(PredicateNotRegisteredError):
        registry.lookup("nope")


def test_all_predicates_preserves_declaration_order() -> None:
    registry = _registry(
        Predicate(predicate_id="b", arity=0),
        Predicate(predicate_id="a", arity=0),
    )
    assert [p.predicate_id for p in registry.all_predicates()] == ["b", "a"]


def test_validate_atom_arity_mismatch() -> None:
    registry = _registry(
        Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    with pytest.raises(PredicateArityMismatchError):
        registry.validate_atom(
            PredicateAtom("bird", ("a", "b"), ("Concept", "Concept"))
        )


def test_validate_atom_argument_type_count_mismatch() -> None:
    registry = _registry(
        Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    with pytest.raises(PredicateArgKindError):
        registry.validate_atom(PredicateAtom("bird", ("a",), ("Concept", "Concept")))


def test_validate_atom_argument_kind_mismatch() -> None:
    registry = _registry(
        Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    with pytest.raises(PredicateArgKindError):
        registry.validate_atom(PredicateAtom("bird", ("a",), ("Wrong",)))


def test_validate_atom_accepts_matching() -> None:
    registry = _registry(
        Predicate(predicate_id="bird", arity=1, arg_types=("Concept",))
    )
    registry.validate_atom(PredicateAtom("bird", ("tweety",), ("Concept",)))


def test_validate_atom_normalizes_kindtype_against_string() -> None:
    registry = _registry(Predicate(predicate_id="t", arity=1, arg_types=("quantity",)))
    registry.validate_atom(PredicateAtom("t", (1.0,), (KindType.QUANTITY,)))


def test_validate_atom_normalizes_case_and_whitespace() -> None:
    registry = _registry(Predicate(predicate_id="t", arity=1, arg_types=("Concept",)))
    registry.validate_atom(PredicateAtom("t", ("x",), ("  concept ",)))


def test_parse_concept_relation_target_may_contain_colons() -> None:
    spec = parse_derived_from("concept.relation:related:ps:concept:45fa8536a97bc81d")
    assert spec.kind == "concept_relation"
    assert spec.relation == "related"
    assert spec.target == "ps:concept:45fa8536a97bc81d"


def test_parse_claim_context_has_no_payload() -> None:
    spec = parse_derived_from("claim.context")
    assert spec.kind == "claim_context"
    assert spec.attribute is None


def test_parse_each_claim_kind() -> None:
    assert parse_derived_from("claim.attribute:value").attribute == "value"
    assert parse_derived_from("claim.condition:t>0").condition == "t>0"
    assert parse_derived_from("claim.role:about").role == "about"
    assert (
        parse_derived_from("claim.provenance:confidence").provenance_field
        == "confidence"
    )


@pytest.mark.parametrize(
    "spec",
    [
        "",
        "concept.relation",
        "concept.relation:is_a",
        "claim.attribute",
        "claim.attribute:",
        "claim.condition",
        "claim.condition:",
        "concept.relation::Bird",
        "concept.relation:is_a:",
        "bogus:thing",
    ],
)
def test_parse_derived_from_malformed_raises(spec: str) -> None:
    with pytest.raises(DerivedFromParseError):
        parse_derived_from(spec)
