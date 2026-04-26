"""Situated assertion identity for the epistemic substrate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.id_types import AssertionId
from propstore.core.relations import RelationConceptRef, RoleBindingSet


@dataclass(frozen=True)
class SituatedAssertion:
    """A relation instance situated in context with applicability and audit ref.

    The identity follows the situated-assertion synthesis: the proposition-like
    atom is relation plus role bindings plus context plus condition. The named
    graph reference is kept for auditability, but it does not participate in
    identity, matching Clark's content/attribution separation and Carroll's
    named-graph carrier discipline.
    """

    relation: RelationConceptRef
    role_bindings: RoleBindingSet
    context: ContextReference
    condition: ConditionRef
    provenance_ref: ProvenanceGraphRef = field(compare=False)

    @property
    def assertion_id(self) -> AssertionId:
        return derive_assertion_id(self.identity_payload())

    def identity_payload(
        self,
    ) -> tuple[
        tuple[str, str],
        tuple[tuple[str, str], ...],
        tuple[str, str],
        tuple[str, str, str],
    ]:
        return (
            self.relation.identity_key(),
            self.role_bindings.identity_payload(),
            self.context.identity_payload(),
            self.condition.identity_payload(),
        )


def derive_assertion_id(identity: object) -> AssertionId:
    rendered = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:32]
    return AssertionId(f"ps:assertion:{digest}")
