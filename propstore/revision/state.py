from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.labels import AssumptionRef, Label


@dataclass(frozen=True)
class RevisionScope:
    bindings: Mapping[str, Any]
    context_id: str | None = None
    branch: str | None = None
    commit: str | None = None


@dataclass(frozen=True)
class BeliefAtom:
    atom_id: str
    kind: str
    payload: Mapping[str, Any]
    label: Label | None = None


@dataclass(frozen=True)
class BeliefBase:
    scope: RevisionScope
    atoms: tuple[BeliefAtom, ...]
    assumptions: tuple[AssumptionRef, ...] = field(default_factory=tuple)
    support_sets: Mapping[str, tuple[tuple[str, ...], ...]] = field(default_factory=dict)
    essential_support: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class RevisionResult:
    revised_base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
