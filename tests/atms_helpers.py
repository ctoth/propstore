"""Shared ATMS test helper stubs."""

from __future__ import annotations

from propstore.context_lifting import LiftingSystem
from propstore.core.assertions import ContextReference


class _ExactMatchSolver:
    def are_disjoint(self, left: list[str], right: list[str]) -> bool:
        return set(left).isdisjoint(right)


class _OverlapSolver:
    def are_disjoint(self, left: list[str], right: list[str]) -> bool:
        if "x == 1" in left and "x > 0" in right:
            return False
        if "x > 0" in left and "x == 1" in right:
            return False
        return set(left).isdisjoint(right)


def leaf_lifting_system(context_id: str) -> LiftingSystem:
    return LiftingSystem(contexts=(ContextReference(context_id),))
