"""Typed document models for authored context YAML files."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import msgspec

from propstore.cel_types import CelExpr
from quire.documents import DocumentStruct
from propstore.context_lifting import LiftingMode


class ContextReferenceDocument(DocumentStruct):
    id: str

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id}


class ContextStructureDocument(DocumentStruct):
    assumptions: tuple[CelExpr, ...] = ()
    parameters: Mapping[str, str] = msgspec.field(default_factory=dict)
    perspective: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.assumptions:
            payload["assumptions"] = list(self.assumptions)
        if self.parameters:
            payload["parameters"] = dict(self.parameters)
        if self.perspective is not None:
            payload["perspective"] = self.perspective
        return payload


class LiftingRuleDocument(DocumentStruct):
    id: str
    source: str
    target: str
    conditions: tuple[CelExpr, ...] = ()
    mode: LiftingMode = LiftingMode.BRIDGE
    justification: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "mode": self.mode.value,
        }
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.justification is not None:
            payload["justification"] = self.justification
        return payload


class ContextDocument(DocumentStruct):
    id: str
    name: str
    description: str | None = None
    structure: ContextStructureDocument = msgspec.field(
        default_factory=ContextStructureDocument
    )
    lifting_rules: tuple[LiftingRuleDocument, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
        }
        if self.description is not None:
            payload["description"] = self.description
        structure = self.structure.to_payload()
        if structure:
            payload["structure"] = structure
        if self.lifting_rules:
            payload["lifting_rules"] = [
                rule.to_payload()
                for rule in self.lifting_rules
            ]
        return payload
