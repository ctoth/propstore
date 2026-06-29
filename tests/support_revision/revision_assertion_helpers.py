from __future__ import annotations

from typing import Any

from propstore.core.active_claims import coerce_active_claim
from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.labels import Label
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.support_revision.state import AssertionAtom


def make_assertion_atom(
    name: str,
    *,
    value: object | None = None,
    concept_id: str | None = None,
    source_paper: str | None = None,
    label: Label | None = None,
) -> AssertionAtom:
    """Build a structural :class:`AssertionAtom` for the revision test suite.

    The atom's identity is the situated assertion (relation + role bindings +
    context + condition); ``name`` and ``value`` vary the structural content so
    distinct names yield distinct ``ps:assertion:`` ids. ``source_paper`` rides
    on the backing claim's attributes, where the entrenchment override matcher
    reads it.
    """
    role_value = name if value is None else value
    assertion = SituatedAssertion(
        relation=RelationConceptRef(concept_id=f"concept_{name}" if concept_id is None else concept_id),
        role_bindings=RoleBindingSet((RoleBinding(role="value", value=str(role_value)),)),
        context=ContextReference("ps:context:test"),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef("urn:propstore:test:provenance"),
    )
    claim_payload: dict[str, Any] = {"id": f"claim_{name}"}
    if source_paper is not None:
        claim_payload["source_paper"] = source_paper
    claim = coerce_active_claim(claim_payload)
    return AssertionAtom(
        atom_id=str(assertion.assertion_id),
        assertion=assertion,
        source_claims=(claim,),
        label=label,
    )
