"""Core label types and helpers for the ATMS-style belief-space kernel."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs
from propstore.core.id_types import (
    AssumptionId,
    ContextId,
    to_assumption_id,
    to_assumption_ids,
    to_context_id,
)


@dataclass(frozen=True, order=True)
class AssumptionRef:
    """Compiled assumption with stable identity for in-memory label use."""

    assumption_id: AssumptionId
    kind: str
    source: str
    cel: CelExpr

    def __post_init__(self) -> None:
        object.__setattr__(self, "cel", to_cel_expr(self.cel))


@dataclass(frozen=True, order=True)
class EnvironmentKey:
    """Immutable set of supporting assumption IDs."""

    assumption_ids: tuple[AssumptionId, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(sorted(dict.fromkeys(to_assumption_ids(self.assumption_ids))))
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


def binding_condition_to_cel(key: str, value: Any) -> CelExpr:
    """Render a query binding into the CEL string used elsewhere in the world model."""
    if isinstance(value, str):
        return to_cel_expr(f"{key} == '{value}'")
    if isinstance(value, bool):
        return to_cel_expr(f"{key} == {'true' if value else 'false'}")
    return to_cel_expr(f"{key} == {value}")


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


def cel_to_binding(cel: str | CelExpr) -> tuple[str, Any] | None:
    """Reverse of binding_condition_to_cel: parse 'key == value' back to (key, value)."""
    parts = str(cel).split(" == ", 1)
    if len(parts) != 2:
        return None
    key, raw = parts[0].strip(), parts[1].strip()
    if not key:
        return None
    if raw.startswith("'") and raw.endswith("'"):
        return (key, raw[1:-1])
    if raw == "true":
        return (key, True)
    if raw == "false":
        return (key, False)
    try:
        if "." in raw:
            return (key, float(raw))
        return (key, int(raw))
    except ValueError:
        return None


def compile_environment_assumptions(
    *,
    bindings: Mapping[str, Any],
    effective_assumptions: Sequence[str | CelExpr] = (),
    context_id: ContextId | str | None = None,
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

    normalized_context_id = None if context_id is None else to_context_id(context_id)
    context_source = normalized_context_id or "<context>"
    for cel in sorted(dict.fromkeys(to_cel_exprs(effective_assumptions))):
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("context", str(context_source), str(cel)),
                kind="context",
                source=str(context_source),
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


def _stable_id(kind: str, source: str, body: str) -> AssumptionId:
    digest = hashlib.sha1(f"{kind}\0{source}\0{body}".encode("utf-8")).hexdigest()[:12]
    return to_assumption_id(f"{kind}:{source}:{digest}")
