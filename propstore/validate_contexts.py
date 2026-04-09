"""Context file validator and hierarchy for the propstore knowledge store."""

from __future__ import annotations

from propstore.context_types import (
    ContextInput,
    LoadedContext,
    coerce_loaded_contexts,
)
from propstore.validate import ValidationResult, load_yaml_entries

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.knowledge_path import KnowledgePath


def load_contexts(contexts_dir: KnowledgePath | None) -> list[LoadedContext]:
    """Load all context YAML files from a contexts subtree."""
    return [
        LoadedContext.from_loaded_entry(entry)
        for entry in load_yaml_entries(contexts_dir)
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


class ContextHierarchy:
    """Query interface over a set of validated contexts."""

    def __init__(self, contexts: list[ContextInput]) -> None:
        typed_contexts = coerce_loaded_contexts(contexts)
        self._contexts = {
            str(context.record.context_id): context.record
            for context in typed_contexts
            if context.record.context_id is not None
        }
        self._parent = {
            context_id: (
                None if record.inherits is None else str(record.inherits)
            )
            for context_id, record in self._contexts.items()
        }
        self._exclusions: set[frozenset[str]] = set()
        for context_id, record in self._contexts.items():
            for exclusion in record.excludes:
                self._exclusions.add(frozenset([context_id, str(exclusion)]))

    def ancestors(self, context_id: str) -> list[str]:
        """Return ancestor chain [parent, grandparent, ...] for a context."""
        result: list[str] = []
        current = self._parent.get(context_id)
        visited: set[str] = set()
        while current is not None and current not in visited:
            result.append(current)
            visited.add(current)
            current = self._parent.get(current)
        return result

    def effective_assumptions(self, context_id: str) -> list[str]:
        """Return all assumptions for a context, including inherited ones."""
        chain = [context_id] + self.ancestors(context_id)
        assumptions: list[str] = []
        for chain_context_id in reversed(chain):
            record = self._contexts.get(chain_context_id)
            if record is None:
                continue
            for assumption in record.assumptions:
                if assumption not in assumptions:
                    assumptions.append(assumption)
        return assumptions

    def are_excluded(self, ctx_a: str, ctx_b: str) -> bool:
        """Check if two contexts are mutually exclusive."""
        return frozenset([ctx_a, ctx_b]) in self._exclusions

    def is_visible(self, querying_ctx: str, claim_ctx: str) -> bool:
        """Check if a claim in claim_ctx is visible when querying querying_ctx."""
        if claim_ctx == querying_ctx:
            return True
        return claim_ctx in self.ancestors(querying_ctx)
