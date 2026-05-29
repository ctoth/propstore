"""Context semantic stage objects and context-boundary coercion."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.cel_types import to_cel_exprs
from propstore.core.assertions.refs import ContextReference
from propstore.families.contexts.lifting import (
    LiftingSystem,
    LiftingMode,
    LiftingRule,
)
from propstore.core.id_types import ContextId
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path as coerce_knowledge_path
from quire.documents import LoadedDocument
from enum import StrEnum

if TYPE_CHECKING:
    from propstore.families.contexts.declaration import ContextDocument


class ContextStage(StrEnum):
    AUTHORED = "context.authored"
    NORMALIZED = "context.normalized"
    BOUND = "context.bound"
    CHECKED = "context.checked"


@dataclass(frozen=True)
class ContextRecord:
    context_id: ContextId | None
    name: str | None
    description: str | None = None
    assumptions: tuple[str, ...] = ()
    parameters: Mapping[str, str] = field(default_factory=dict)
    perspective: str | None = None
    lifting_rules: tuple[LiftingRule, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.context_id is not None:
            payload["id"] = str(self.context_id)
        if self.name is not None:
            payload["name"] = self.name
        if self.description is not None:
            payload["description"] = self.description
        if self.assumptions:
            payload["assumptions"] = list(self.assumptions)
        if self.parameters:
            payload["parameters"] = dict(self.parameters)
        if self.perspective is not None:
            payload["perspective"] = self.perspective
        if self.lifting_rules:
            payload["lifting_rules"] = [
                {
                    "id": rule.id,
                    "source": str(rule.source.id),
                    "target": str(rule.target.id),
                    "conditions": list(rule.conditions),
                    "mode": rule.mode.value,
                    **(
                        {}
                        if rule.justification is None
                        else {"justification": rule.justification}
                    ),
                }
                for rule in self.lifting_rules
            ]
        return payload


@dataclass(frozen=True)
class LoadedContext:
    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    record: ContextRecord

    @classmethod
    def from_record(
        cls,
        *,
        filename: str,
        record: ContextRecord,
        source_path: KnowledgePath | Path | None = None,
        knowledge_root: KnowledgePath | Path | None = None,
    ) -> LoadedContext:
        return cls(
            filename=filename,
            source_path=None if source_path is None else coerce_knowledge_path(source_path),
            knowledge_root=(
                None
                if knowledge_root is None
                else coerce_knowledge_path(knowledge_root)
            ),
            record=record,
        )

    @classmethod
    def from_payload(
        cls,
        *,
        filename: str,
        source_path: KnowledgePath | Path | None,
        data: Mapping[str, Any] | None,
        knowledge_root: KnowledgePath | Path | None = None,
    ) -> LoadedContext:
        return cls.from_record(
            filename=filename,
            record=parse_context_record(data),
            source_path=source_path,
            knowledge_root=knowledge_root,
        )

    @classmethod
    def from_loaded_document(
        cls,
        document: LoadedDocument[ContextDocument],
    ) -> LoadedContext:
        return cls.from_record(
            filename=document.filename,
            source_path=document.artifact_path,
            knowledge_root=document.store_root,
            record=parse_context_record_document(document.document),
        )


@dataclass(frozen=True)
class ContextAuthoredSet:
    contexts: tuple[LoadedContext, ...]


@dataclass(frozen=True)
class ContextNormalizedSet:
    contexts: tuple[LoadedContext, ...]


@dataclass(frozen=True)
class ContextBoundGraph:
    contexts: tuple[LoadedContext, ...]
    lifting_system: LiftingSystem


@dataclass(frozen=True)
class ContextCheckedGraph:
    contexts: tuple[LoadedContext, ...]
    lifting_system: LiftingSystem


def parse_context_record(data: Mapping[str, Any] | None) -> ContextRecord:
    payload = {} if data is None else dict(data)
    if "structure" in payload:
        raise ValueError("Context record 'structure' is no longer supported")

    raw_context_id = payload.get("id")
    context_id = (
        ContextId(raw_context_id)
        if isinstance(raw_context_id, str) and raw_context_id
        else None
    )

    raw_name = payload.get("name")
    name = raw_name if isinstance(raw_name, str) and raw_name else None

    raw_description = payload.get("description")
    description = (
        raw_description
        if isinstance(raw_description, str) and raw_description
        else None
    )

    raw_assumptions = payload.get("assumptions")
    if raw_assumptions is None:
        raw_assumptions = ()
    elif isinstance(raw_assumptions, Sequence) and not isinstance(raw_assumptions, str):
        raw_assumptions = raw_assumptions
    else:
        raise ValueError("Context record 'assumptions' must be a sequence when present")
    assumptions = tuple(
        assumption
        for assumption in raw_assumptions
        if isinstance(assumption, str) and assumption
    )

    raw_parameters = payload.get("parameters")
    if raw_parameters is None:
        parameters = {}
    elif isinstance(raw_parameters, Mapping):
        parameters = {
            str(key): str(value)
            for key, value in raw_parameters.items()
        }
    else:
        raise ValueError("Context record 'parameters' must be a mapping when present")
    raw_perspective = payload.get("perspective")
    perspective = (
        raw_perspective
        if isinstance(raw_perspective, str) and raw_perspective
        else None
    )
    lifting_rules = _parse_lifting_rules(payload.get("lifting_rules"))

    return ContextRecord(
        context_id=context_id,
        name=name,
        description=description,
        assumptions=assumptions,
        parameters=parameters,
        perspective=perspective,
        lifting_rules=lifting_rules,
    )


def _parse_context_reference_id(raw: object) -> ContextId | None:
    if isinstance(raw, str) and raw:
        return ContextId(raw)
    if isinstance(raw, Mapping):
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id:
            return ContextId(raw_id)
    return None


def _parse_lifting_rules(raw_rules: object) -> tuple[LiftingRule, ...]:
    if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, str):
        return ()
    rules: list[LiftingRule] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, Mapping):
            continue
        raw_id = raw_rule.get("id")
        source_id = _parse_context_reference_id(raw_rule.get("source"))
        target_id = _parse_context_reference_id(raw_rule.get("target"))
        if not isinstance(raw_id, str) or not raw_id or source_id is None or target_id is None:
            continue
        raw_conditions = raw_rule.get("conditions")
        conditions = (
            raw_conditions
            if isinstance(raw_conditions, Sequence) and not isinstance(raw_conditions, str)
            else ()
        )
        raw_mode = raw_rule.get("mode")
        mode = (
            LiftingMode(raw_mode)
            if isinstance(raw_mode, str) and raw_mode
            else LiftingMode.BRIDGE
        )
        raw_justification = raw_rule.get("justification")
        justification = raw_justification if isinstance(raw_justification, str) else None
        rules.append(
            LiftingRule(
                id=raw_id,
                source=ContextReference(id=source_id),
                target=ContextReference(id=target_id),
                conditions=to_cel_exprs(str(condition) for condition in conditions),
                mode=mode,
                justification=justification,
            )
        )
    return tuple(rules)


def parse_context_record_document(data: ContextDocument) -> ContextRecord:
    return ContextRecord(
        context_id=ContextId(data.id),
        name=data.name,
        description=data.description,
        assumptions=tuple(str(assumption) for assumption in (data.assumptions or ())),
        parameters={} if data.parameters is None else dict(data.parameters),
        perspective=data.perspective,
        lifting_rules=tuple(
            LiftingRule(
                id=rule.id,
                source=ContextReference(id=ContextId(rule.source)),
                target=ContextReference(id=ContextId(rule.target)),
                conditions=rule.conditions or (),
                mode=LiftingMode(rule.mode),
                justification=rule.justification,
            )
            for rule in (data.lifting_rules or ())
        ),
    )


def loaded_contexts_to_lifting_system(
    contexts: Sequence[LoadedContext],
) -> LiftingSystem:
    return LiftingSystem(
        contexts=tuple(
            ContextReference(id=context.record.context_id)
            for context in contexts
            if context.record.context_id is not None
        ),
        lifting_rules=tuple(
            rule
            for context in contexts
            for rule in context.record.lifting_rules
        ),
        context_assumptions={
            context.record.context_id: to_cel_exprs(context.record.assumptions)
            for context in contexts
            if context.record.context_id is not None
        },
    )
