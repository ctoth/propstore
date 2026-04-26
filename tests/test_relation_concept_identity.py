from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.id_types import ConceptId
from propstore.core.relations import (
    BOOTSTRAP_RELATION_IDS,
    RelationConceptRef,
    RelationPropertyAssertion,
    RelationPropertyKind,
    RelationPropertySet,
    RoleBinding,
    RoleBindingSet,
    RoleDefinition,
    RoleSignature,
)


EXPECTED_BOOTSTRAP_RELATIONS = frozenset({
    "relation_concept",
    "role",
    "has_role",
    "role_domain",
    "role_range",
    "subtype_of",
    "instance_of",
    "contextualizes",
    "condition_applies",
    "supports",
    "undercuts",
    "rebuts",
    "base_rate_for",
    "calibrates",
    "published_in",
})


def test_bootstrap_relation_vocabulary_matches_workstream() -> None:
    assert BOOTSTRAP_RELATION_IDS == EXPECTED_BOOTSTRAP_RELATIONS


def test_relation_identity_is_a_concept_reference_not_a_bare_predicate() -> None:
    relation = RelationConceptRef(
        concept_id=ConceptId("ps:concept:relation:published_in"),
        lexical_sense_id="lemon:sense:published-in",
        description_kind_id="framenet:Publishing",
    )

    assert not isinstance(relation, str)
    assert relation.identity_key() == (
        "relation_concept",
        "ps:concept:relation:published_in",
    )


def test_relation_identity_ignores_lexical_rendering_metadata() -> None:
    first = RelationConceptRef(
        concept_id=ConceptId("ps:concept:relation:published_in"),
        lexical_sense_id="lemon:sense:published-in",
        description_kind_id="framenet:Publishing",
    )
    second = RelationConceptRef(
        concept_id=ConceptId("ps:concept:relation:published_in"),
        lexical_sense_id="lemon:sense:appeared-in",
        description_kind_id="framenet:Publication",
    )

    assert first.identity_key() == second.identity_key()


def test_role_signature_rejects_duplicate_roles() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))

    with pytest.raises(ValueError, match="duplicate role"):
        RoleSignature(
            relation=relation,
            role_definitions=(
                RoleDefinition(
                    role="paper",
                    domain=ConceptId("ps:concept:class:publication_event"),
                    range=ConceptId("ps:concept:class:paper"),
                ),
                RoleDefinition(
                    role="paper",
                    domain=ConceptId("ps:concept:class:publication_event"),
                    range=ConceptId("ps:concept:class:paper"),
                ),
            ),
        )


def test_role_definition_requires_domain_and_range() -> None:
    with pytest.raises(ValueError, match="role domain"):
        RoleDefinition(
            role="paper",
            domain="",
            range=ConceptId("ps:concept:class:paper"),
        )
    with pytest.raises(ValueError, match="role range"):
        RoleDefinition(
            role="paper",
            domain=ConceptId("ps:concept:class:publication_event"),
            range="",
        )


def test_role_signature_identity_includes_domain_and_range() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    signature = RoleSignature(
        relation=relation,
        role_definitions=(
            RoleDefinition(
                role="venue",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:venue"),
            ),
            RoleDefinition(
                role="paper",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:paper"),
            ),
        ),
    )

    assert signature.identity_payload() == (
        ("relation_concept", "ps:concept:relation:published_in"),
        (
            (
                "paper",
                "ps:concept:class:publication_event",
                "ps:concept:class:paper",
            ),
            (
                "venue",
                "ps:concept:class:publication_event",
                "ps:concept:class:venue",
            ),
        ),
    )


def test_role_binding_validation_rejects_missing_required_role() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    signature = _published_in_signature(relation)
    bindings = RoleBindingSet((RoleBinding("paper", "ps:concept:paper:cimiano-2016"),))

    with pytest.raises(ValueError, match="missing role"):
        signature.validate_bindings(bindings)


def test_role_binding_validation_rejects_unknown_role() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    signature = _published_in_signature(relation)
    bindings = RoleBindingSet((
        RoleBinding("paper", "ps:concept:paper:cimiano-2016"),
        RoleBinding("publisher", "ps:concept:publisher:w3c"),
        RoleBinding("venue", "ps:concept:venue:w3c-community-report"),
    ))

    with pytest.raises(ValueError, match="unknown role"):
        signature.validate_bindings(bindings)


@given(
    st.permutations((
        RoleBinding("paper", "ps:concept:paper:buitelaar-2011"),
        RoleBinding("venue", "ps:concept:venue:tia-2011"),
    )),
)
def test_role_binding_set_canonicalizes_role_order(
    bindings: tuple[RoleBinding, ...],
) -> None:
    assert RoleBindingSet(bindings).identity_payload() == (
        ("paper", "ps:concept:paper:buitelaar-2011"),
        ("venue", "ps:concept:venue:tia-2011"),
    )


def test_inverse_property_requires_target_relation() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))

    with pytest.raises(ValueError, match="inverse target"):
        RelationPropertyAssertion(
            relation=relation,
            kind=RelationPropertyKind.INVERSE_OF,
        )


@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        min_size=1,
        max_size=12,
    ),
    st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
        min_size=1,
        max_size=12,
    ),
)
def test_inverse_property_is_an_involution(left_id: str, right_id: str) -> None:
    left = RelationConceptRef(ConceptId(f"ps:concept:relation:{left_id}"))
    right = RelationConceptRef(ConceptId(f"ps:concept:relation:{right_id}"))
    assertion = RelationPropertyAssertion(
        relation=left,
        kind=RelationPropertyKind.INVERSE_OF,
        target=right,
    )

    assert assertion.inverse().inverse() == assertion


def test_symmetric_relation_canonicalizes_binary_values() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:co_occurs_with"))
    properties = RelationPropertySet((
        RelationPropertyAssertion(
            relation=relation,
            kind=RelationPropertyKind.SYMMETRIC,
        ),
    ))

    assert properties.canonicalize_binary_values(relation, "zeta", "alpha") == (
        "alpha",
        "zeta",
    )


def test_non_symmetric_relation_preserves_binary_value_order() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:supports"))
    properties = RelationPropertySet(())

    assert properties.canonicalize_binary_values(relation, "zeta", "alpha") == (
        "zeta",
        "alpha",
    )


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=4),
            st.integers(min_value=0, max_value=4),
        ),
        max_size=8,
    ),
)
def test_transitive_closure_contains_authored_edges(
    edges: set[tuple[int, int]],
) -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:subtype_of"))
    properties = RelationPropertySet((
        RelationPropertyAssertion(
            relation=relation,
            kind=RelationPropertyKind.TRANSITIVE,
        ),
    ))

    closure = properties.transitive_closure(
        relation,
        frozenset((str(left), str(right)) for left, right in edges),
    )

    assert frozenset((str(left), str(right)) for left, right in edges) <= closure


def _published_in_signature(relation: RelationConceptRef) -> RoleSignature:
    return RoleSignature(
        relation=relation,
        role_definitions=(
            RoleDefinition(
                role="paper",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:paper"),
            ),
            RoleDefinition(
                role="venue",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:venue"),
            ),
        ),
    )
