from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from propstore.cel_types import to_cel_expr
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claim
from propstore.core.id_types import AssumptionId, ContextId, to_assumption_id, to_assumption_ids, to_context_id
from propstore.core.labels import AssumptionRef, Label
from propstore.support_revision.explanation_types import (
    EntrenchmentReason,
    RevisionAtomDetail,
    coerce_entrenchment_reason,
    coerce_revision_atom_detail,
)


def coerce_assumption_ref(payload: AssumptionRef | Mapping[str, Any]) -> AssumptionRef:
    if isinstance(payload, AssumptionRef):
        return payload
    assumption_id = payload.get("assumption_id") or payload.get("id")
    if assumption_id is None:
        raise ValueError("Assumption atom requires 'assumption_id' or 'id'")
    return AssumptionRef(
        assumption_id=to_assumption_id(assumption_id),
        cel=to_cel_expr(str(payload.get("cel") or "")),
        kind=str(payload.get("kind") or ""),
        source=str(payload.get("source") or ""),
    )


@dataclass(frozen=True)
class ClaimAtom:
    atom_id: str
    claim: ActiveClaim
    label: Label | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim", coerce_active_claim(self.claim))

    @property
    def claim_id(self) -> str:
        return str(self.claim.claim_id)


@dataclass(frozen=True)
class AssumptionAtom:
    atom_id: str
    assumption: AssumptionRef
    label: Label | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumption", coerce_assumption_ref(self.assumption))


BeliefAtom = ClaimAtom | AssumptionAtom


def is_claim_atom(atom: BeliefAtom) -> TypeGuard[ClaimAtom]:
    return isinstance(atom, ClaimAtom)


def is_assumption_atom(atom: BeliefAtom) -> TypeGuard[AssumptionAtom]:
    return isinstance(atom, AssumptionAtom)


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
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "explanation",
            {
                str(atom_id): coerce_revision_atom_detail(detail)
                for atom_id, detail in self.explanation.items()
            },
        )


@dataclass(frozen=True)
class RevisionEpisode:
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    accepted_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_atom_ids", tuple(str(atom_id) for atom_id in self.target_atom_ids))
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "explanation",
            {
                str(atom_id): coerce_revision_atom_detail(detail)
                for atom_id, detail in self.explanation.items()
            },
        )


@dataclass(frozen=True)
class EpistemicState:
    scope: RevisionScope
    base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    ranked_atom_ids: tuple[str, ...]
    ranking: Mapping[str, int] = field(default_factory=dict)
    entrenchment_reasons: Mapping[str, EntrenchmentReason] = field(default_factory=dict)
    history: tuple[RevisionEpisode, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "ranked_atom_ids", tuple(str(atom_id) for atom_id in self.ranked_atom_ids))
        object.__setattr__(
            self,
            "ranking",
            {str(atom_id): int(rank) for atom_id, rank in self.ranking.items()},
        )
        object.__setattr__(
            self,
            "entrenchment_reasons",
            {
                str(atom_id): coerce_entrenchment_reason(reason)
                for atom_id, reason in self.entrenchment_reasons.items()
            },
        )
        object.__setattr__(self, "history", tuple(self.history))
