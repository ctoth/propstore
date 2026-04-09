"""Canonical context dataclasses and context-boundary coercion."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from propstore.core.id_types import ContextId, to_context_id
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.loaded import LoadedEntry


@dataclass(frozen=True)
class ContextRecord:
    context_id: ContextId | None
    name: str | None
    description: str | None = None
    inherits: ContextId | None = None
    assumptions: tuple[str, ...] = ()
    excludes: tuple[ContextId, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.context_id is not None:
            payload["id"] = str(self.context_id)
        if self.name is not None:
            payload["name"] = self.name
        if self.description is not None:
            payload["description"] = self.description
        if self.inherits is not None:
            payload["inherits"] = str(self.inherits)
        if self.assumptions:
            payload["assumptions"] = list(self.assumptions)
        if self.excludes:
            payload["excludes"] = [str(context_id) for context_id in self.excludes]
        return payload


@dataclass(frozen=True)
class LoadedContext:
    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    record: ContextRecord

    @classmethod
    def from_payload(
        cls,
        *,
        filename: str,
        source_path: KnowledgePath | Path | None,
        data: Mapping[str, Any] | None,
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
            record=parse_context_record(data),
        )

    @classmethod
    def from_loaded_entry(cls, entry: LoadedEntry) -> LoadedContext:
        return cls.from_payload(
            filename=entry.filename,
            source_path=entry.source_path,
            knowledge_root=entry.knowledge_root,
            data=entry.data,
        )

    def to_loaded_entry(self) -> LoadedEntry:
        return LoadedEntry(
            filename=self.filename,
            source_path=self.source_path,
            knowledge_root=self.knowledge_root,
            data=self.record.to_payload(),
        )


ContextInput = LoadedContext | LoadedEntry


def parse_context_record(data: Mapping[str, Any] | None) -> ContextRecord:
    payload = {} if data is None else dict(data)

    raw_context_id = payload.get("id")
    context_id = (
        to_context_id(raw_context_id)
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

    raw_inherits = payload.get("inherits")
    inherits = (
        to_context_id(raw_inherits)
        if isinstance(raw_inherits, str) and raw_inherits
        else None
    )

    assumptions = tuple(
        assumption
        for assumption in (
            payload.get("assumptions")
            if isinstance(payload.get("assumptions"), Sequence)
            and not isinstance(payload.get("assumptions"), str)
            else ()
        )
        if isinstance(assumption, str) and assumption
    )

    excludes = tuple(
        to_context_id(exclusion)
        for exclusion in (
            payload.get("excludes")
            if isinstance(payload.get("excludes"), Sequence)
            and not isinstance(payload.get("excludes"), str)
            else ()
        )
        if isinstance(exclusion, str) and exclusion
    )

    return ContextRecord(
        context_id=context_id,
        name=name,
        description=description,
        inherits=inherits,
        assumptions=assumptions,
        excludes=excludes,
    )


def coerce_loaded_context(context: ContextInput) -> LoadedContext:
    if isinstance(context, LoadedContext):
        return context
    return LoadedContext.from_loaded_entry(context)


def coerce_loaded_contexts(contexts: Sequence[ContextInput]) -> list[LoadedContext]:
    return [coerce_loaded_context(context) for context in contexts]
