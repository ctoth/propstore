from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from quire.hashing import canonical_json_bytes

from propstore.cel_types import to_cel_expr
from propstore.core.active_claims import ActiveClaim, coerce_active_claim
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import (
    AssertionId,
    AssumptionId,
    ContextId,
    to_assertion_id,
    to_assumption_id,
    to_assumption_ids,
    to_context_id,
)
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
class AssertionAtom:
    atom_id: str
    assertion: SituatedAssertion
    source_claims: tuple[ActiveClaim, ...] = field(default_factory=tuple)
    label: Label | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.assertion, SituatedAssertion):
            raise TypeError("assertion atom requires a SituatedAssertion")
        assertion_id = self.assertion.assertion_id
        object.__setattr__(self, "atom_id", str(assertion_id))
        object.__setattr__(
            self,
            "source_claims",
            tuple(coerce_active_claim(claim) for claim in self.source_claims),
        )

    @property
    def assertion_id(self) -> AssertionId:
        return to_assertion_id(self.assertion.assertion_id)

    @property
    def primary_source_claim(self) -> ActiveClaim | None:
        return self.source_claims[0] if self.source_claims else None


@dataclass(frozen=True)
class AssumptionAtom:
    atom_id: str
    assumption: AssumptionRef
    label: Label | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumption", coerce_assumption_ref(self.assumption))


BeliefAtom = AssertionAtom | AssumptionAtom


def is_assertion_atom(atom: BeliefAtom) -> TypeGuard[AssertionAtom]:
    return isinstance(atom, AssertionAtom)


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
class FormalRevisionDecisionReport:
    operation: str
    policy: str
    input_formula_ids: tuple[str, ...] = ()
    accepted_formula_ids: tuple[str, ...] = ()
    rejected_formula_ids: tuple[str, ...] = ()
    epistemic_state_hash: str | None = None
    budget_failure: str | None = None
    trace: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_formula_ids", tuple(str(item) for item in self.input_formula_ids))
        object.__setattr__(self, "accepted_formula_ids", tuple(str(item) for item in self.accepted_formula_ids))
        object.__setattr__(self, "rejected_formula_ids", tuple(str(item) for item in self.rejected_formula_ids))
        object.__setattr__(self, "trace", dict(self.trace))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FormalRevisionDecisionReport:
        return cls(
            operation=str(payload.get("operation") or ""),
            policy=str(payload.get("policy") or ""),
            input_formula_ids=tuple(str(item) for item in (payload.get("input_formula_ids") or ())),
            accepted_formula_ids=tuple(str(item) for item in (payload.get("accepted_formula_ids") or ())),
            rejected_formula_ids=tuple(str(item) for item in (payload.get("rejected_formula_ids") or ())),
            epistemic_state_hash=(
                None
                if payload.get("epistemic_state_hash") is None
                else str(payload.get("epistemic_state_hash"))
            ),
            budget_failure=(
                None
                if payload.get("budget_failure") is None
                else str(payload.get("budget_failure"))
            ),
            trace=dict(payload.get("trace") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "operation": self.operation,
            "policy": self.policy,
            "input_formula_ids": list(self.input_formula_ids),
            "accepted_formula_ids": list(self.accepted_formula_ids),
            "rejected_formula_ids": list(self.rejected_formula_ids),
            "trace": dict(self.trace),
        }
        if self.epistemic_state_hash is not None:
            data["epistemic_state_hash"] = self.epistemic_state_hash
        if self.budget_failure is not None:
            data["budget_failure"] = self.budget_failure
        return data


@dataclass(frozen=True)
class SupportRevisionRealization:
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = ()
    source_claim_ids: tuple[str, ...] = ()
    reasons: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)
    snapshot_hash: str | None = None
    journal_metadata: Mapping[str, Any] = field(default_factory=dict)
    replay_status: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(self, "source_claim_ids", tuple(str(claim_id) for claim_id in self.source_claim_ids))
        object.__setattr__(
            self,
            "reasons",
            {
                str(atom_id): coerce_revision_atom_detail(detail)
                for atom_id, detail in self.reasons.items()
            },
        )
        object.__setattr__(self, "journal_metadata", dict(self.journal_metadata))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SupportRevisionRealization:
        reasons_payload = payload.get("reasons") or {}
        if not isinstance(reasons_payload, Mapping):
            raise ValueError("support revision realization requires mapping 'reasons'")
        return cls(
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (payload.get("incision_set") or ())),
            source_claim_ids=tuple(str(claim_id) for claim_id in (payload.get("source_claim_ids") or ())),
            reasons={
                str(atom_id): coerce_revision_atom_detail(detail)
                for atom_id, detail in reasons_payload.items()
            },
            snapshot_hash=None if payload.get("snapshot_hash") is None else str(payload.get("snapshot_hash")),
            journal_metadata=dict(payload.get("journal_metadata") or {}),
            replay_status=None if payload.get("replay_status") is None else str(payload.get("replay_status")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "rejected_atom_ids": list(self.rejected_atom_ids),
            "incision_set": list(self.incision_set),
            "source_claim_ids": list(self.source_claim_ids),
            "reasons": {
                atom_id: detail.to_dict()
                for atom_id, detail in self.reasons.items()
            },
            "journal_metadata": dict(self.journal_metadata),
        }
        if self.snapshot_hash is not None:
            data["snapshot_hash"] = self.snapshot_hash
        if self.replay_status is not None:
            data["replay_status"] = self.replay_status
        return data


@dataclass(frozen=True)
class RevisionResult:
    revised_base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)
    decision: FormalRevisionDecisionReport | None = None
    realization: SupportRevisionRealization | None = None

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
        if self.realization is None:
            object.__setattr__(
                self,
                "realization",
                SupportRevisionRealization(
                    accepted_atom_ids=self.accepted_atom_ids,
                    rejected_atom_ids=self.rejected_atom_ids,
                    incision_set=self.incision_set,
                    reasons=self.explanation,
                ),
            )


@dataclass(frozen=True)
class RevisionEvent:
    operation: str
    pre_state_hash: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    decision: FormalRevisionDecisionReport | None = None
    realization: SupportRevisionRealization | None = None
    policy_snapshot: Mapping[str, str] = field(default_factory=dict)
    replay_status: str | None = None
    realization_failure: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation", str(self.operation))
        object.__setattr__(self, "pre_state_hash", str(self.pre_state_hash))
        object.__setattr__(self, "target_atom_ids", tuple(str(atom_id) for atom_id in self.target_atom_ids))
        object.__setattr__(
            self,
            "policy_snapshot",
            {str(key): str(value) for key, value in self.policy_snapshot.items()},
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RevisionEvent:
        decision_payload = payload.get("decision")
        realization_payload = payload.get("realization")
        if decision_payload is not None and not isinstance(decision_payload, Mapping):
            raise ValueError("revision event requires mapping 'decision'")
        if realization_payload is not None and not isinstance(realization_payload, Mapping):
            raise ValueError("revision event requires mapping 'realization'")
        policy_payload = payload.get("policy_snapshot") or {}
        if not isinstance(policy_payload, Mapping):
            raise ValueError("revision event requires mapping 'policy_snapshot'")
        event = cls(
            operation=str(payload.get("operation") or ""),
            pre_state_hash=str(payload.get("pre_state_hash") or ""),
            input_atom_id=None if payload.get("input_atom_id") is None else str(payload.get("input_atom_id")),
            target_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("target_atom_ids") or ())),
            decision=(
                None
                if decision_payload is None
                else FormalRevisionDecisionReport.from_mapping(decision_payload)
            ),
            realization=(
                None
                if realization_payload is None
                else SupportRevisionRealization.from_mapping(realization_payload)
            ),
            policy_snapshot={str(key): str(value) for key, value in policy_payload.items()},
            replay_status=None if payload.get("replay_status") is None else str(payload.get("replay_status")),
            realization_failure=(
                None
                if payload.get("realization_failure") is None
                else str(payload.get("realization_failure"))
            ),
        )
        recorded_hash = payload.get("content_hash")
        if recorded_hash is not None and str(recorded_hash) != event.content_hash:
            raise ValueError("revision event content_hash does not match payload")
        return event

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self._content_payload())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "operation": self.operation,
            "pre_state_hash": self.pre_state_hash,
            "target_atom_ids": list(self.target_atom_ids),
            "policy_snapshot": dict(self.policy_snapshot),
        }
        if self.input_atom_id is not None:
            data["input_atom_id"] = self.input_atom_id
        if self.decision is not None:
            data["decision"] = self.decision.to_dict()
        if self.realization is not None:
            data["realization"] = self.realization.to_dict()
        if self.replay_status is not None:
            data["replay_status"] = self.replay_status
        if self.realization_failure is not None:
            data["realization_failure"] = self.realization_failure
        return data


class RevisionRealizationFailure(RuntimeError):
    def __init__(self, event: RevisionEvent) -> None:
        super().__init__(event.realization_failure or "revision realization failed")
        self.event = event


class RevisionMergeRequiredFailure(RuntimeError):
    def __init__(
        self,
        *,
        reason: str = "merge_required",
        parent_commits: tuple[str, ...] = (),
    ) -> None:
        self.reason = str(reason)
        self.parent_commits = tuple(str(commit) for commit in parent_commits)
        message = self.reason
        if self.parent_commits:
            message += f": {', '.join(self.parent_commits)}"
        super().__init__(message)


@dataclass(frozen=True)
class RevisionEpisode:
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    accepted_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_atom_ids: tuple[str, ...] = field(default_factory=tuple)
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)
    event: RevisionEvent | None = None

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

    def to_canonical_dict(self) -> dict[str, Any]:
        from propstore.support_revision.snapshot_types import EpistemicStateSnapshot

        return EpistemicStateSnapshot.from_state(self).to_dict()
