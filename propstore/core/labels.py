"""Core label types for the ATMS-style belief-space kernel.

Moved from world/labelled.py to fix the inverted layer dependency
(core must not import from world).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, order=True)
class AssumptionRef:
    """Compiled assumption with stable identity for in-memory label use."""

    assumption_id: str
    kind: str
    source: str
    cel: str


@dataclass(frozen=True, order=True)
class EnvironmentKey:
    """Immutable set of supporting assumption IDs."""

    assumption_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(sorted(dict.fromkeys(self.assumption_ids)))
        object.__setattr__(self, "assumption_ids", normalized)

    def union(self, other: EnvironmentKey) -> EnvironmentKey:
        return EnvironmentKey(self.assumption_ids + other.assumption_ids)

    def subsumes(self, other: EnvironmentKey) -> bool:
        return set(self.assumption_ids).issubset(other.assumption_ids)


@dataclass(frozen=True)
class NogoodSet:
    """Minimal inconsistent environments."""

    environments: tuple[EnvironmentKey, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "environments",
            normalize_environments(self.environments),
        )

    def excludes(self, environment: EnvironmentKey) -> bool:
        return any(nogood.subsumes(environment) for nogood in self.environments)


def normalize_environments(
    environments: Iterable[EnvironmentKey],
    *,
    nogoods: NogoodSet | None = None,
) -> tuple[EnvironmentKey, ...]:
    """Deduplicate, prune supersets, and drop known-nogood environments."""
    unique = {
        env.assumption_ids: env
        for env in environments
        if nogoods is None or not nogoods.excludes(env)
    }
    ordered = sorted(unique.values(), key=lambda env: (len(env.assumption_ids), env.assumption_ids))
    minimal: list[EnvironmentKey] = []
    for candidate in ordered:
        if any(existing.subsumes(candidate) for existing in minimal):
            continue
        minimal.append(candidate)
    return tuple(minimal)


@dataclass(frozen=True)
class Label:
    """Minimal antichain of supporting environments."""

    environments: tuple[EnvironmentKey, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "environments",
            normalize_environments(self.environments),
        )

    @classmethod
    def empty(cls) -> Label:
        """Unconditional support: the empty environment."""
        return cls((EnvironmentKey(()),))

    @classmethod
    def singleton(cls, assumption: AssumptionRef) -> Label:
        return cls((EnvironmentKey((assumption.assumption_id,)),))


def binding_condition_to_cel(key: str, value: Any) -> str:
    """Render a query binding into the CEL string used elsewhere in the world model."""
    if isinstance(value, str):
        return f"{key} == '{value}'"
    if isinstance(value, bool):
        return f"{key} == {'true' if value else 'false'}"
    return f"{key} == {value}"
