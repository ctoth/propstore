"""Query interface over a set of validated contexts."""

from __future__ import annotations

from propstore.context_types import (
    ContextInput,
    coerce_loaded_contexts,
)


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
