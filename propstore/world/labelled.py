"""Internal ATMS-style label kernel for compiled belief-space support."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from propstore.core.id_types import AssumptionId, ContextId, to_assumption_id, to_context_id
# Canonical definitions live in core/labels.py; re-exported here
# for backward compatibility within the world layer.
from propstore.core.labels import (  # noqa: F401
    AssumptionRef,
    EnvironmentKey,
    Label,
    NogoodSet,
    binding_condition_to_cel,
    normalize_environments,
)


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


def cel_to_binding(cel: str) -> tuple[str, Any] | None:
    """Reverse of binding_condition_to_cel: parse 'key == value' back to (key, value).

    Returns None if the CEL expression is not a simple binding equality.
    """
    parts = cel.split(" == ", 1)
    if len(parts) != 2:
        return None
    key, raw = parts[0].strip(), parts[1].strip()
    if not key:
        return None
    # String literal: 'value'
    if raw.startswith("'") and raw.endswith("'"):
        return (key, raw[1:-1])
    # Boolean
    if raw == "true":
        return (key, True)
    if raw == "false":
        return (key, False)
    # Numeric
    try:
        if "." in raw:
            return (key, float(raw))
        return (key, int(raw))
    except ValueError:
        return None


def compile_environment_assumptions(
    *,
    bindings: Mapping[str, Any],
    effective_assumptions: Sequence[str] = (),
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
    for cel in sorted(dict.fromkeys(effective_assumptions)):
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("context", str(context_source), str(cel)),
                kind="context",
                source=str(context_source),
                cel=str(cel),
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
