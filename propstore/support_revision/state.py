from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeGuard

import msgspec
from quire.canonical import canonical_json_bytes

from propstore.core.active_claims import ActiveClaim
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.environment import AssumptionRef
from propstore.core.id_types import (
    AssertionId,
    AssumptionId,
    ContextId,
    to_assertion_id,
    to_assumption_ids,
    to_context_id,
)
from propstore.core.labels import Label
from propstore.core.scalars import ScalarValue
from propstore.reporting import json_ready
from propstore.support_revision.decision_trace import DecisionTrace, RankingProvenance
from propstore.support_revision.integrity_constraints import IntegrityConstraintSpec
from propstore.support_revision.explanation_types import (
    EntrenchmentReason,
    RevisionAtomDetail,
)


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


class AssertionAtom(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    tag="assertion",
):
    atom_id: str
    assertion: SituatedAssertion
    source_claims: tuple[ActiveClaim, ...] = ()
    label: Label | None = None

    def __post_init__(self) -> None:
        expected_atom_id = str(self.assertion.assertion_id)
        if self.atom_id != expected_atom_id:
            raise ValueError("assertion atom id does not match situated assertion")

    @property
    def assertion_id(self) -> AssertionId:
        return to_assertion_id(self.assertion.assertion_id)

    @property
    def primary_source_claim(self) -> ActiveClaim | None:
        return self.source_claims[0] if self.source_claims else None


class AssumptionAtom(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    tag="assumption",
):
    atom_id: str
    assumption: AssumptionRef
    label: Label | None = None


BeliefAtom = AssertionAtom | AssumptionAtom


def is_assertion_atom(atom: BeliefAtom) -> TypeGuard[AssertionAtom]:
    return isinstance(atom, AssertionAtom)


def is_assumption_atom(atom: BeliefAtom) -> TypeGuard[AssumptionAtom]:
    return isinstance(atom, AssumptionAtom)


class RevisionScope(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    bindings: dict[str, ScalarValue]
    context_id: ContextId | None = None
    branch: str | None = None
    commit: str | None = None
    merge_parent_commits: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "context_id",
            None if self.context_id is None else to_context_id(self.context_id),
        )
        object.__setattr__(
            self, "merge_parent_commits", tuple(self.merge_parent_commits)
        )


class BeliefBase(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    scope: RevisionScope
    atoms: tuple[BeliefAtom, ...]
    assumptions: tuple[AssumptionRef, ...] = ()
    support_sets: dict[str, tuple[tuple[AssumptionId, ...], ...]] = msgspec.field(
        default_factory=dict[str, tuple[tuple[AssumptionId, ...], ...]]
    )
    essential_support: dict[str, tuple[AssumptionId, ...]] = msgspec.field(
        default_factory=dict[str, tuple[AssumptionId, ...]]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "atoms", tuple(self.atoms))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(
            self,
            "support_sets",
            {
                str(atom_id): tuple(
                    to_assumption_ids(support_set) for support_set in support_sets
                )
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


class FormalRevisionDecisionReport(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    operation: str
    policy: str
    input_formula_ids: tuple[str, ...] = ()
    accepted_formula_ids: tuple[str, ...] = ()
    rejected_formula_ids: tuple[str, ...] = ()
    epistemic_state_hash: str | None = None
    budget_failure: str | None = None
    # What the operator recorded about how it reached this decision — a tagged
    # union, not a bag. Expand and contract record nothing.
    trace: DecisionTrace | None = None
    # How the ranking this decision used was obtained. A sibling fact about the
    # decision, not part of the operator's trace, and it carries the typed
    # ProvenanceStatus rather than the string "defaulted".
    ranking_provenance: RankingProvenance | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "input_formula_ids",
            tuple(str(item) for item in self.input_formula_ids),
        )
        object.__setattr__(
            self,
            "accepted_formula_ids",
            tuple(str(item) for item in self.accepted_formula_ids),
        )
        object.__setattr__(
            self,
            "rejected_formula_ids",
            tuple(str(item) for item in self.rejected_formula_ids),
        )


class SupportRevisionRealization(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = ()
    source_claim_ids: tuple[str, ...] = ()
    reasons: dict[str, RevisionAtomDetail] = msgspec.field(
        default_factory=dict[str, RevisionAtomDetail]
    )
    snapshot_hash: str | None = None
    replay_status: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_atom_ids",
            tuple(str(atom_id) for atom_id in self.accepted_atom_ids),
        )
        object.__setattr__(
            self,
            "rejected_atom_ids",
            tuple(str(atom_id) for atom_id in self.rejected_atom_ids),
        )
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(
            self,
            "source_claim_ids",
            tuple(str(claim_id) for claim_id in self.source_claim_ids),
        )
        object.__setattr__(
            self,
            "reasons",
            {str(atom_id): detail for atom_id, detail in self.reasons.items()},
        )


@dataclass(frozen=True)
class RevisionResult:
    revised_base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = field(default_factory=tuple)
    explanation: Mapping[str, RevisionAtomDetail] = field(
        default_factory=dict[str, RevisionAtomDetail]
    )
    decision: FormalRevisionDecisionReport | None = None
    realization: SupportRevisionRealization | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_atom_ids",
            tuple(str(atom_id) for atom_id in self.accepted_atom_ids),
        )
        object.__setattr__(
            self,
            "rejected_atom_ids",
            tuple(str(atom_id) for atom_id in self.rejected_atom_ids),
        )
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(
            self,
            "explanation",
            {str(atom_id): detail for atom_id, detail in self.explanation.items()},
        )
        if self.realization is None:
            object.__setattr__(
                self,
                "realization",
                SupportRevisionRealization(
                    accepted_atom_ids=self.accepted_atom_ids,
                    rejected_atom_ids=self.rejected_atom_ids,
                    incision_set=self.incision_set,
                    reasons=dict(self.explanation),
                ),
            )


class RevisionEvent(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    operation: str
    pre_state_hash: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    decision: FormalRevisionDecisionReport | None = None
    realization: SupportRevisionRealization | None = None
    policy_snapshot: dict[str, str] = msgspec.field(default_factory=dict[str, str])
    replay_status: str | None = None
    realization_failure: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation", str(self.operation))
        object.__setattr__(self, "pre_state_hash", str(self.pre_state_hash))
        object.__setattr__(
            self,
            "target_atom_ids",
            tuple(str(atom_id) for atom_id in self.target_atom_ids),
        )
        object.__setattr__(
            self,
            "policy_snapshot",
            {str(key): str(value) for key, value in self.policy_snapshot.items()},
        )

    @property
    def content_hash(self) -> str:
        """Fingerprint of the event's own fields.

        Derived from the struct itself through the one canonical lowering, not
        from a hand-written payload builder: a second spelling of the event's
        shape could silently drift from the fields it claims to hash, and a
        field added to the struct would then leave the fingerprint unchanged.
        """

        return hashlib.sha256(canonical_json_bytes(json_ready(self))).hexdigest()


class RevisionRealizationFailure(RuntimeError):
    def __init__(self, event: RevisionEvent) -> None:
        super().__init__(event.realization_failure or "revision realization failed")
        self.event = event


class RevisionMergeRequiredFailure(ValueError):
    def __init__(
        self,
        *,
        reason: str = "merge_required",
        parent_commits: tuple[str, ...] = (),
        decision_report: FormalRevisionDecisionReport | None = None,
        profile_atom_ids: tuple[tuple[str, ...], ...] = (),
        integrity_constraint: IntegrityConstraintSpec | None = None,
        selected_worlds_hash: str | None = None,
        event: RevisionEvent | None = None,
    ) -> None:
        self.reason = str(reason)
        self.parent_commits = tuple(str(commit) for commit in parent_commits)
        self.decision_report = decision_report
        self.profile_atom_ids = tuple(
            tuple(str(atom_id) for atom_id in profile) for profile in profile_atom_ids
        )
        self.integrity_constraint = integrity_constraint
        self.selected_worlds_hash = (
            None if selected_worlds_hash is None else str(selected_worlds_hash)
        )
        self.event = event
        message = (
            "merge point requires IC merge"
            if self.reason == "merge_required"
            else self.reason
        )
        if self.parent_commits:
            message += f": {', '.join(self.parent_commits)}"
        super().__init__(message)


class RevisionEpisode(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
):
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: dict[str, RevisionAtomDetail] = msgspec.field(
        default_factory=dict[str, RevisionAtomDetail]
    )
    event: RevisionEvent | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "target_atom_ids",
            tuple(str(atom_id) for atom_id in self.target_atom_ids),
        )
        object.__setattr__(
            self,
            "accepted_atom_ids",
            tuple(str(atom_id) for atom_id in self.accepted_atom_ids),
        )
        object.__setattr__(
            self,
            "rejected_atom_ids",
            tuple(str(atom_id) for atom_id in self.rejected_atom_ids),
        )
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(
            self,
            "explanation",
            {str(atom_id): detail for atom_id, detail in self.explanation.items()},
        )


class EpistemicState(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
):
    scope: RevisionScope
    base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    ranked_atom_ids: tuple[str, ...]
    ranking: dict[str, int] = msgspec.field(default_factory=dict[str, int])
    entrenchment_reasons: dict[str, EntrenchmentReason] = msgspec.field(
        default_factory=dict[str, EntrenchmentReason]
    )
    history: tuple[RevisionEpisode, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_atom_ids",
            tuple(str(atom_id) for atom_id in self.accepted_atom_ids),
        )
        object.__setattr__(
            self,
            "ranked_atom_ids",
            tuple(str(atom_id) for atom_id in self.ranked_atom_ids),
        )
        object.__setattr__(
            self,
            "ranking",
            {str(atom_id): int(rank) for atom_id, rank in self.ranking.items()},
        )
        object.__setattr__(
            self,
            "entrenchment_reasons",
            {
                str(atom_id): reason
                for atom_id, reason in self.entrenchment_reasons.items()
            },
        )
        object.__setattr__(self, "history", tuple(self.history))

    def to_canonical_dict(self) -> dict[str, Any]:
        from quire.documents import to_document_builtins

        payload = to_document_builtins(self)
        if not _is_mapping(payload):
            raise TypeError("epistemic state must encode as a mapping")
        return dict(payload)
