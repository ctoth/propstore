"""Typed claim surface for repository merge semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from quire.documents import document_to_payload

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssertionId, ContextId, ProvenanceGraphId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.identity.logical_ids import format_logical_id


@dataclass(frozen=True)
class MergeClaim:
    document: ClaimDocument
    branch_origin: str | None = None

    @property
    def artifact_id(self) -> str:
        assert self.document.artifact_id is not None
        return self.document.artifact_id

    @property
    def claim_type(self) -> str | None:
        return self.document.type

    @property
    def value_concept_id(self) -> str:
        if (
            isinstance(self.document.output_concept, str)
            and self.document.output_concept
        ):
            return self.document.output_concept
        if (
            isinstance(self.document.target_concept, str)
            and self.document.target_concept
        ):
            return self.document.target_concept
        for concept_id in self.document.concepts:
            if isinstance(concept_id, str) and concept_id:
                return concept_id
        return ""

    @property
    def logical_ids(self) -> tuple[str, ...]:
        return tuple(
            formatted
            for logical_id in self.document.logical_ids
            if (
                formatted := format_logical_id(
                    cast(dict[str, Any], document_to_payload(logical_id))
                )
            )
            is not None
        )

    @property
    def primary_logical_id(self) -> str | None:
        logical_ids = self.logical_ids
        if logical_ids:
            return logical_ids[0]
        return None

    @property
    def value(self) -> Any:
        return self.document.value

    @property
    def assertion(self) -> SituatedAssertion:
        return SituatedAssertion(
            relation=RelationConceptRef(
                f"ps:relation:claim:{self.claim_type or 'unknown'}"
            ),
            role_bindings=RoleBindingSet(
                (
                    RoleBinding(
                        "subject", self.value_concept_id or "ps:concept:unscoped"
                    ),
                    RoleBinding(
                        "content", _stable_json(_semantic_payload(self.document))
                    ),
                )
            ),
            context=ContextReference(ContextId(self.document.context.id)),
            condition=ConditionRef.unconditional(),
            provenance_ref=_provenance_ref(self),
        )

    @property
    def assertion_id(self) -> AssertionId:
        return self.assertion.assertion_id

    def get(self, key: str, default: object = None) -> object:
        return self.to_payload(include_id_alias=True).get(key, default)

    def __getitem__(self, key: str) -> object:
        return self.to_payload(include_id_alias=True)[key]


def _provenance_ref(claim: MergeClaim) -> ProvenanceGraphRef:
    return ProvenanceGraphRef(
        ProvenanceGraphId(
            f"urn:propstore:claim-provenance:{_digest(claim.provenance_payload())}"
        )
    )


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def _digest(value: object) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()
