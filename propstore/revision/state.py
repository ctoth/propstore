from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claim
from propstore.core.id_types import AssumptionId, ContextId, to_assumption_ids, to_context_id
from propstore.core.labels import AssumptionRef, Label
from propstore.revision.explanation_types import (
    EntrenchmentReason,
    RevisionAtomDetail,
    coerce_entrenchment_reason,
    coerce_revision_atom_detail,
)


@dataclass(frozen=True)
class ClaimAtomPayload:
    claim: ActiveClaim

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim", coerce_active_claim(self.claim))

    @classmethod
    def from_input(cls, claim: ActiveClaimInput) -> ClaimAtomPayload:
        return cls(claim=coerce_active_claim(claim))

    @property
    def claim_id(self) -> str:
        return str(self.claim.claim_id)

    def to_dict(self) -> dict[str, Any]:
        return self.claim.to_dict()


@dataclass(frozen=True)
class AssumptionAtomPayload:
    assumption_id: str
    cel: str | None = None
    kind: str | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "assumption_id": self.assumption_id,
        }
        if self.cel is not None:
            data["cel"] = self.cel
        if self.kind is not None:
            data["kind"] = self.kind
        if self.source is not None:
            data["source"] = self.source
        return data


BeliefAtomPayload = ClaimAtomPayload | AssumptionAtomPayload


def coerce_claim_atom_payload(payload: ClaimAtomPayload | ActiveClaimInput) -> ClaimAtomPayload:
    if isinstance(payload, ClaimAtomPayload):
        return payload
    return ClaimAtomPayload(claim=coerce_active_claim(payload))


def coerce_assumption_atom_payload(
    payload: AssumptionAtomPayload | AssumptionRef | Mapping[str, Any],
) -> AssumptionAtomPayload:
    if isinstance(payload, AssumptionAtomPayload):
        return payload
    if isinstance(payload, AssumptionRef):
        return AssumptionAtomPayload(
            assumption_id=str(payload.assumption_id),
            cel=payload.cel,
            kind=payload.kind,
            source=payload.source,
        )
    assumption_id = payload.get("assumption_id") or payload.get("id")
    if assumption_id is None:
        raise ValueError("Assumption atom payload requires 'assumption_id' or 'id'")
    return AssumptionAtomPayload(
        assumption_id=str(assumption_id),
        cel=None if payload.get("cel") is None else str(payload.get("cel")),
        kind=None if payload.get("kind") is None else str(payload.get("kind")),
        source=None if payload.get("source") is None else str(payload.get("source")),
    )


def claim_atom_payload(atom: BeliefAtom) -> ClaimAtomPayload | None:
    payload = atom.payload
    return payload if isinstance(payload, ClaimAtomPayload) else None


def assumption_atom_payload(atom: BeliefAtom) -> AssumptionAtomPayload | None:
    payload = atom.payload
    return payload if isinstance(payload, AssumptionAtomPayload) else None


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
    payload: BeliefAtomPayload
    label: Label | None = None

    def __post_init__(self) -> None:
        if self.kind == "claim":
            object.__setattr__(self, "payload", coerce_claim_atom_payload(self.payload))
            return
        if self.kind == "assumption":
            object.__setattr__(self, "payload", coerce_assumption_atom_payload(self.payload))
            return
        raise ValueError(f"Unsupported belief atom kind: {self.kind}")


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
