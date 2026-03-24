"""Internal ATMS-style label kernel for compiled belief-space support."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
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


@dataclass(frozen=True)
class JustificationRecord:
    """Compiled justification result for a conclusion."""

    conclusion: str
    antecedents: tuple[Label, ...]
    label: Label

    @classmethod
    def from_antecedents(
        cls,
        conclusion: str,
        antecedents: Sequence[Label],
        *,
        nogoods: NogoodSet | None = None,
    ) -> JustificationRecord:
        return cls(
            conclusion=conclusion,
            antecedents=tuple(antecedents),
            label=combine_labels(*antecedents, nogoods=nogoods),
        )


class SupportQuality(Enum):
    """How faithfully the current belief-space activation can be labeled."""

    EXACT = "exact"
    SEMANTIC_COMPATIBLE = "semantic_compatible"
    CONTEXT_VISIBLE_ONLY = "context_visible_only"
    MIXED = "mixed"


def binding_condition_to_cel(key: str, value: Any) -> str:
    """Render a query binding into the CEL string used elsewhere in the world model."""
    if isinstance(value, str):
        return f"{key} == '{value}'"
    if isinstance(value, bool):
        return f"{key} == {'true' if value else 'false'}"
    return f"{key} == {value}"


def compile_environment_assumptions(
    *,
    bindings: Mapping[str, Any],
    effective_assumptions: Sequence[str] = (),
    context_id: str | None = None,
) -> tuple[AssumptionRef, ...]:
    """Compile bindings and inherited context assumptions into stable refs."""
    compiled: list[AssumptionRef] = []

    for key in sorted(bindings):
        value = bindings[key]
        rendered_value = json.dumps(value, sort_keys=True, default=str)
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("binding", key, rendered_value),
                kind="binding",
                source=key,
                cel=binding_condition_to_cel(key, value),
            )
        )

    context_source = context_id or "<context>"
    for cel in sorted(dict.fromkeys(effective_assumptions)):
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("context", context_source, cel),
                kind="context",
                source=context_source,
                cel=cel,
            )
        )

    return tuple(sorted(compiled, key=lambda ref: ref.assumption_id))


def combine_labels(
    *labels: Label,
    nogoods: NogoodSet | None = None,
) -> Label:
    """Combine antecedent labels by cross-product union."""
    if not labels:
        return Label.empty()

    environments = (EnvironmentKey(()),)
    for label in labels:
        if not label.environments:
            return Label(())
        combined: list[EnvironmentKey] = []
        for left in environments:
            for right in label.environments:
                combined.append(left.union(right))
        environments = normalize_environments(combined, nogoods=nogoods)
        if not environments:
            return Label(())
    return Label(tuple(environments))


def merge_labels(
    labels: Iterable[Label],
    *,
    nogoods: NogoodSet | None = None,
) -> Label:
    """Merge alternative supports for the same datum into one normalized label."""
    environments: list[EnvironmentKey] = []
    for label in labels:
        environments.extend(label.environments)
    return Label(tuple(normalize_environments(environments, nogoods=nogoods)))


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


def _stable_id(kind: str, source: str, body: str) -> str:
    digest = hashlib.sha1(f"{kind}\0{source}\0{body}".encode("utf-8")).hexdigest()[:12]
    return f"{kind}:{source}:{digest}"
