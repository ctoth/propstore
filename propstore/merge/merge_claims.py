"""Typed claim surface for repository merge semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from propstore.core.assertions.refs import ConditionRef, ContextReference, ProvenanceGraphRef
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssertionId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.families.claims.documents import ClaimDocument
from propstore.families.identity.logical_ids import format_logical_id


@dataclass(frozen=True)
class MergeClaim:
    document: ClaimDocument
    branch_origin: str | None = None

    @classmethod
    def from_document(
        cls,
        document: ClaimDocument,
        *,
        branch_origin: str | None = None,
    ) -> MergeClaim | None:
        artifact_id = document.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            return None
        return cls(document=document, branch_origin=branch_origin)

    @property
    def artifact_id(self) -> str:
        assert self.document.artifact_id is not None
        return self.document.artifact_id

    @property
    def claim_type(self) -> str | None:
        return self.document.type

    @property
    def value_concept_id(self) -> str:
        if isinstance(self.document.output_concept, str) and self.document.output_concept:
            return self.document.output_concept
        if isinstance(self.document.target_concept, str) and self.document.target_concept:
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
            if (formatted := format_logical_id(logical_id.to_payload())) is not None
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
            relation=RelationConceptRef(f"ps:relation:claim:{self.claim_type or 'unknown'}"),
            role_bindings=RoleBindingSet(
                (
                    RoleBinding("subject", self.value_concept_id or "ps:concept:unscoped"),
                    RoleBinding("content", _stable_json(_semantic_payload(self.document))),
                )
            ),
            context=ContextReference(self.document.context.id),
            condition=_condition_ref(tuple(self.document.conditions)),
            provenance_ref=_provenance_ref(self),
        )

    @property
    def assertion_id(self) -> AssertionId:
        return self.assertion.assertion_id

    def get(self, key: str, default: object = None) -> object:
        return self.to_payload(include_id_alias=True).get(key, default)

    def __getitem__(self, key: str) -> object:
        return self.to_payload(include_id_alias=True)[key]

    def provenance_payload(self) -> dict[str, Any]:
        provenance = (
            {}
            if self.document.provenance is None
            else dict(self.document.provenance.to_payload())
        )
        if self.branch_origin is not None:
            provenance["branch_origin"] = self.branch_origin
        return provenance

    def to_payload(
        self,
        *,
        include_branch_origin: bool = True,
        include_id_alias: bool = False,
    ) -> dict[str, Any]:
        payload = self.document.to_payload()
        if include_id_alias and "id" not in payload and self.document.artifact_id is not None:
            payload["id"] = self.document.artifact_id
        if include_branch_origin:
            payload["provenance"] = self.provenance_payload()
        elif self.document.provenance is not None:
            payload["provenance"] = dict(self.document.provenance.to_payload())
        return payload


def _semantic_payload(document: ClaimDocument) -> dict[str, Any]:
    payload = document.to_payload()
    for key in (
        "artifact_id",
        "artifact_code",
        "id",
        "logical_ids",
        "version_id",
        "stances",
        "context",
    ):
        payload.pop(key, None)
    return payload


def _condition_ref(conditions: tuple[object, ...]) -> ConditionRef:
    if not conditions:
        return ConditionRef.unconditional()
    digest = _digest(tuple(str(condition) for condition in conditions))
    return ConditionRef(
        id=f"ps:condition:{digest}",
        registry_fingerprint=f"claim-condition-source:{digest}",
    )


def _provenance_ref(claim: MergeClaim) -> ProvenanceGraphRef:
    return ProvenanceGraphRef(
        f"urn:propstore:claim-provenance:{_digest(claim.provenance_payload())}"
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
