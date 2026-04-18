"""Context file validator for the propstore knowledge store."""

from __future__ import annotations

from propstore.artifacts.documents.contexts import ContextDocument
from quire.documents import load_document_dir
from propstore.context_types import (
    ContextInput,
    LoadedContext,
    coerce_loaded_contexts,
)
from propstore.diagnostics import ValidationResult

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quire.tree_path import TreePath as KnowledgePath


def load_contexts(contexts_dir: KnowledgePath | None) -> list[LoadedContext]:
    """Load all context YAML files from a contexts subtree."""
    return load_document_dir(
        contexts_dir,
        ContextDocument,
        wrapper=LoadedContext.from_loaded_document,
    )


def validate_contexts(contexts: list[ContextInput]) -> ValidationResult:
    """Validate context files for required fields and lifting-rule references."""
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

        for rule in record.lifting_rules:
            if str(rule.source.id) not in all_ids:
                result.errors.append(
                    f"{context.filename}: lifting rule '{rule.id}' references "
                    f"nonexistent source context '{rule.source.id}'"
                )
            if str(rule.target.id) not in all_ids:
                result.errors.append(
                    f"{context.filename}: lifting rule '{rule.id}' references "
                    f"nonexistent target context '{rule.target.id}'"
                )

    return result
