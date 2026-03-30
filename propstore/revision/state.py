from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import AssumptionId, ContextId, to_assumption_ids, to_context_id
from propstore.core.labels import AssumptionRef, Label


@dataclass(frozen=True)
class RevisionScope:
    bindings: Mapping[str, Any]
    context_id: ContextId | None = None
    branch: str | None = None
    commit: str | None = None
    merge_parent_commits: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "context_id",
            None if self.context_id is None else to_context_id(self.context_id),
        )
        object.__setattr__(self, "merge_parent_commits", tuple(self.merge_parent_commits))


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
    support_sets: Mapping[str, tuple[tuple[AssumptionId, ...], ...]] = field(default_factory=dict)
    essential_support: Mapping[str, tuple[AssumptionId, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "atoms", tuple(self.atoms))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(
            self,
            "support_sets",
            {
                str(atom_id): tuple(to_assumption_ids(support_set) for support_set in support_sets)
                for atom_id, support_sets in self.support_sets.items()
            },
        )
        object.__setattr__(
            self,
            "essential_support",
            {
                str(atom_id): to_assumption_ids(support)
                for atom_id, support in self.essential_support.items()
            },
        )


@dataclass(frozen=True)
class RevisionResult:
    revised_base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class RevisionEpisode:
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    accepted_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class EpistemicState:
    scope: RevisionScope
    base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    ranked_atom_ids: tuple[str, ...]
    ranking: Mapping[str, int] = field(default_factory=dict)
    entrenchment_reasons: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    history: tuple[RevisionEpisode, ...] = field(default_factory=tuple)
