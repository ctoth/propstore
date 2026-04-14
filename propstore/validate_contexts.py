"""Context file validator and hierarchy for the propstore knowledge store."""

from __future__ import annotations

from propstore.context_types import (
    ContextDocument,
    ContextInput,
    LoadedContext,
    coerce_loaded_contexts,
)
from propstore.artifacts.schema import load_document
from propstore.diagnostics import ValidationResult

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.knowledge_path import KnowledgePath


def load_contexts(contexts_dir: KnowledgePath | None) -> list[LoadedContext]:
    """Load all context YAML files from a contexts subtree."""
    if contexts_dir is None or not contexts_dir.is_dir():
        return []
    knowledge_root = contexts_dir.parent if contexts_dir.name else contexts_dir
    return [
        LoadedContext.from_loaded_document(
            load_document(
                entry,
                ContextDocument,
                knowledge_root=knowledge_root,
            )
        )
        for entry in contexts_dir.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]


def validate_contexts(contexts: list[ContextInput]) -> ValidationResult:
    """Validate context files for required fields, references, and cycles."""
    typed_contexts = coerce_loaded_contexts(contexts)
    result = ValidationResult()
    seen_ids: dict[str, str] = {}
    all_ids: set[str] = set()

    for context in typed_contexts:
        if context.record.context_id is not None:
            all_ids.add(str(context.record.context_id))

    for context in typed_contexts:
        record = context.record
        context_id = None if record.context_id is None else str(record.context_id)

        if context_id is None:
            result.errors.append(f"{context.filename}: context missing 'id'")
            continue

        if record.name is None:
            result.errors.append(f"{context.filename}: context '{context_id}' missing 'name'")

        if context_id in seen_ids:
            result.errors.append(
                f"{context.filename}: duplicate context ID '{context_id}' "
                f"(also in {seen_ids[context_id]})"
            )
        else:
            seen_ids[context_id] = context.filename

        if record.inherits is not None and str(record.inherits) not in all_ids:
            result.errors.append(
                f"{context.filename}: context '{context_id}' inherits nonexistent context '{record.inherits}'"
            )

        for exclusion in record.excludes:
            if str(exclusion) not in all_ids:
                result.errors.append(
                    f"{context.filename}: context '{context_id}' excludes nonexistent context '{exclusion}'"
                )

    parent_map: dict[str, str | None] = {}
    for context in typed_contexts:
        if context.record.context_id is None:
            continue
        parent_map[str(context.record.context_id)] = (
            None if context.record.inherits is None else str(context.record.inherits)
        )

    for context_id in parent_map:
        visited: set[str] = set()
        current = context_id
        while current is not None:
            if current in visited:
                result.errors.append(
                    f"Inheritance cycle detected involving context '{context_id}'"
                )
                break
            visited.add(current)
            current = parent_map.get(current)

    return result
