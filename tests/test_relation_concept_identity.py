from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.id_types import ConceptId
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
)


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


@pytest.mark.property
@given(
    st.permutations(
        (
            RoleBinding("paper", "ps:concept:paper:buitelaar-2011"),
            RoleBinding("venue", "ps:concept:venue:tia-2011"),
        )
    ),
)
def test_role_binding_set_canonicalizes_role_order(
    bindings: tuple[RoleBinding, ...],
) -> None:
    assert RoleBindingSet(bindings).identity_payload() == (
        ("paper", "ps:concept:paper:buitelaar-2011"),
        ("venue", "ps:concept:venue:tia-2011"),
    )
