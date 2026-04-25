from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.id_types import ConceptId
from propstore.core.relations import (
    BOOTSTRAP_RELATION_IDS,
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
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
        RoleSignature(relation=relation, roles=("paper", "paper"))


def test_role_binding_validation_rejects_missing_required_role() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    signature = RoleSignature(relation=relation, roles=("paper", "venue"))
    bindings = RoleBindingSet((RoleBinding("paper", "ps:concept:paper:cimiano-2016"),))

    with pytest.raises(ValueError, match="missing role"):
        signature.validate_bindings(bindings)


def test_role_binding_validation_rejects_unknown_role() -> None:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    signature = RoleSignature(relation=relation, roles=("paper", "venue"))
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
