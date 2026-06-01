from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.assertions.codec import AssertionCanonicalRecord
from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import ConceptId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet


def _published_in_assertion() -> SituatedAssertion:
    return SituatedAssertion(
        relation=RelationConceptRef(ConceptId("ps:concept:relation:published_in")),
        role_bindings=RoleBindingSet(
            (
                RoleBinding("paper", "ps:concept:paper:clark-2014"),
                RoleBinding("venue", "ps:concept:venue:j-biomed-semantics"),
            )
        ),
        context=ContextReference("ctx_literature"),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef("urn:propstore:provenance:source"),
    )
