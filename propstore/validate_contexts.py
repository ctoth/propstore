"""Context file validator and hierarchy for the propstore knowledge store.

Loads knowledge/contexts/*.yaml files, validates references and structure,
and provides a ContextHierarchy for querying inheritance, exclusion, and visibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typing import TYPE_CHECKING

from propstore.validate import ValidationResult, load_yaml_entries

if TYPE_CHECKING:
    from propstore.knowledge_path import KnowledgePath


from propstore.loaded import LoadedEntry


def load_contexts(contexts_dir: KnowledgePath | Path | None) -> list[LoadedEntry]:
    """Load all context YAML files from a contexts subtree."""
    return load_yaml_entries(contexts_dir)


def validate_contexts(contexts: list[LoadedEntry]) -> ValidationResult:
    """Validate context files for required fields, references, and cycles."""
    result = ValidationResult()
    seen_ids: dict[str, str] = {}  # id -> filename
    all_ids: set[str] = set()

    # First pass: collect all IDs
    for ctx in contexts:
        cid = ctx.data.get("id")
        if cid:
            all_ids.add(cid)

    # Second pass: validate each context
    for ctx in contexts:
        d = ctx.data

        # Required fields
        cid = d.get("id")
        if not cid:
            result.errors.append(f"{ctx.filename}: context missing 'id'")
            continue

        name = d.get("name")
        if not name:
            result.errors.append(f"{ctx.filename}: context '{cid}' missing 'name'")

        # Duplicate ID check
        if cid in seen_ids:
            result.errors.append(
                f"{ctx.filename}: duplicate context ID '{cid}' "
                f"(also in {seen_ids[cid]})")
        else:
            seen_ids[cid] = ctx.filename

        # Inherits reference
        inherits = d.get("inherits")
        if inherits and inherits not in all_ids:
            result.errors.append(
                f"{ctx.filename}: context '{cid}' inherits nonexistent context '{inherits}'")

        # Excludes references
        excludes = d.get("excludes") or []
        for exc in excludes:
            if exc not in all_ids:
                result.errors.append(
                    f"{ctx.filename}: context '{cid}' excludes nonexistent context '{exc}'")

    # Cycle detection in inheritance
    parent_map: dict[str, str | None] = {}
    for ctx in contexts:
        cid = ctx.data.get("id")
        if cid:
            parent_map[cid] = ctx.data.get("inherits")

    for cid in parent_map:
        visited: set[str] = set()
        current = cid
        while current is not None:
            if current in visited:
                result.errors.append(
                    f"Inheritance cycle detected involving context '{cid}'")
                break
            visited.add(current)
            current = parent_map.get(current)

    return result


class ContextHierarchy:
    """Query interface over a set of validated contexts."""

    def __init__(self, contexts: list[LoadedEntry]) -> None:
        self._contexts: dict[str, dict] = {}
        self._parent: dict[str, str | None] = {}
        self._exclusions: set[frozenset[str]] = set()

        for ctx in contexts:
            cid = ctx.data.get("id")
            if not cid:
                continue
            self._contexts[cid] = ctx.data
            self._parent[cid] = ctx.data.get("inherits")
            for exc in ctx.data.get("excludes") or []:
                self._exclusions.add(frozenset([cid, exc]))

    def ancestors(self, context_id: str) -> list[str]:
        """Return ancestor chain [parent, grandparent, ...] for a context."""
        result = []
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
        assumptions = []
        # Collect in reverse order (root first) so child assumptions come last
        for cid in reversed(chain):
            ctx_data = self._contexts.get(cid, {})
            for a in ctx_data.get("assumptions") or []:
                if a not in assumptions:
                    assumptions.append(a)
        return assumptions

    def are_excluded(self, ctx_a: str, ctx_b: str) -> bool:
        """Check if two contexts are mutually exclusive."""
        return frozenset([ctx_a, ctx_b]) in self._exclusions

    def is_visible(self, querying_ctx: str, claim_ctx: str) -> bool:
        """Check if a claim in claim_ctx is visible when querying querying_ctx.

        A claim is visible if claim_ctx is the querying context itself
        or one of its ancestors.
        """
        if claim_ctx == querying_ctx:
            return True
        return claim_ctx in self.ancestors(querying_ctx)
