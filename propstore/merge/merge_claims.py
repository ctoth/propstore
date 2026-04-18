"""Typed claim surface for repository merge semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from propstore.artifacts.documents.claims import ClaimDocument
from propstore.identity import format_logical_id


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
    def concept_id(self) -> str:
        if isinstance(self.document.concept, str) and self.document.concept:
            return self.document.concept
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
