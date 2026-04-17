from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from propstore.cel_types import to_cel_expr
from propstore.core.active_claims import coerce_active_claim
from propstore.core.id_types import to_assumption_id, to_assumption_ids, to_context_id
from propstore.core.labels import AssumptionRef, EnvironmentKey, Label
from propstore.support_revision.explanation_types import (
    EntrenchmentReason,
    RevisionAtomDetail,
    coerce_entrenchment_reason,
    coerce_revision_atom_detail,
)
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    EpistemicState,
    AssumptionAtom,
    ClaimAtom,
    RevisionEpisode,
    RevisionScope,
    is_assumption_atom,
    is_claim_atom,
)


def _environment_key_from_mapping(data: Mapping[str, Any]) -> EnvironmentKey:
    return EnvironmentKey(to_assumption_ids(data.get("assumption_ids") or ()))


def _environment_key_to_dict(environment: EnvironmentKey) -> dict[str, Any]:
    return {
        "assumption_ids": list(environment.assumption_ids),
    }


def _label_from_mapping(data: Mapping[str, Any] | None) -> Label | None:
    if not data:
        return None
    return Label(
        tuple(
            _environment_key_from_mapping(entry)
            for entry in (data.get("environments") or ())
            if isinstance(entry, Mapping)
        )
    )


def _label_to_dict(label: Label | None) -> dict[str, Any] | None:
    if label is None:
        return None
    return {
        "environments": [
            _environment_key_to_dict(environment)
            for environment in label.environments
        ]
    }


def _assumption_ref_from_mapping(data: Mapping[str, Any]) -> AssumptionRef:
    return AssumptionRef(
        assumption_id=to_assumption_id(data.get("assumption_id") or ""),
        kind=str(data.get("kind") or ""),
        source=str(data.get("source") or ""),
        cel=to_cel_expr(str(data.get("cel") or "")),
    )


def _assumption_ref_to_dict(assumption: AssumptionRef) -> dict[str, Any]:
    return {
        "assumption_id": assumption.assumption_id,
        "kind": assumption.kind,
        "source": assumption.source,
        "cel": assumption.cel,
    }


def _scope_from_mapping(data: Mapping[str, Any]) -> RevisionScope:
    return RevisionScope(
        bindings=dict(data.get("bindings") or {}),
        context_id=None if data.get("context_id") is None else to_context_id(data.get("context_id")),
        branch=None if data.get("branch") is None else str(data.get("branch")),
        commit=None if data.get("commit") is None else str(data.get("commit")),
        merge_parent_commits=tuple(str(item) for item in (data.get("merge_parent_commits") or ())),
    )


def _required_mapping(data: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ValueError(f"Support revision snapshot requires mapping '{field_name}'")
    return data


def _scope_to_dict(scope: RevisionScope) -> dict[str, Any]:
    data: dict[str, Any] = {
        "bindings": dict(scope.bindings),
    }
    if scope.context_id is not None:
        data["context_id"] = str(scope.context_id)
    if scope.branch is not None:
        data["branch"] = scope.branch
    if scope.commit is not None:
        data["commit"] = scope.commit
    if scope.merge_parent_commits:
        data["merge_parent_commits"] = list(scope.merge_parent_commits)
    return data


def _belief_atom_from_mapping(data: Mapping[str, Any]) -> BeliefAtom:
    kind = str(data.get("kind") or "")
    payload_data = data.get("payload")
    atom_id = str(data.get("atom_id") or "")
    label = _label_from_mapping(data.get("label") if isinstance(data.get("label"), Mapping) else None)
    if kind == "claim":
        if not isinstance(payload_data, Mapping):
            raise ValueError("Claim atom snapshot requires mapping payload")
        return ClaimAtom(atom_id=atom_id, claim=coerce_active_claim(payload_data), label=label)
    if kind == "assumption":
        if not isinstance(payload_data, Mapping):
            raise ValueError("Assumption atom snapshot requires mapping payload")
        return AssumptionAtom(atom_id=atom_id, assumption=_assumption_ref_from_mapping(payload_data), label=label)
    raise ValueError(f"Unsupported belief atom snapshot kind: {kind}")


def _belief_atom_to_dict(atom: BeliefAtom) -> dict[str, Any]:
    if isinstance(atom, ClaimAtom):
        payload = atom.claim.to_dict()
        kind = "claim"
    else:
        assert isinstance(atom, AssumptionAtom)
        payload = {
            "assumption_id": atom.assumption.assumption_id,
            "cel": atom.assumption.cel,
            "kind": atom.assumption.kind,
            "source": atom.assumption.source,
        }
        kind = "assumption"
    data: dict[str, Any] = {
        "atom_id": atom.atom_id,
        "kind": kind,
        "payload": payload,
    }
    label = _label_to_dict(atom.label)
    if label is not None:
        data["label"] = label
    return data


def _belief_base_from_mapping(data: Mapping[str, Any]) -> BeliefBase:
    support_sets_payload = data.get("support_sets") or {}
    essential_support_payload = data.get("essential_support") or {}
    return BeliefBase(
        scope=_scope_from_mapping(_required_mapping(data.get("scope"), "scope")),
        atoms=tuple(
            _belief_atom_from_mapping(item)
            for item in (data.get("atoms") or ())
            if isinstance(item, Mapping)
        ),
        assumptions=tuple(
            _assumption_ref_from_mapping(item)
            for item in (data.get("assumptions") or ())
            if isinstance(item, Mapping)
        ),
        support_sets={
            str(atom_id): tuple(
                to_assumption_ids(support_set)
                for support_set in support_sets
            )
            for atom_id, support_sets in support_sets_payload.items()
        },
        essential_support={
            str(atom_id): to_assumption_ids(support)
            for atom_id, support in essential_support_payload.items()
        },
    )


def _belief_base_to_dict(base: BeliefBase) -> dict[str, Any]:
    return {
        "scope": _scope_to_dict(base.scope),
        "atoms": [_belief_atom_to_dict(atom) for atom in base.atoms],
        "assumptions": [_assumption_ref_to_dict(assumption) for assumption in base.assumptions],
        "support_sets": {
            atom_id: [list(support_set) for support_set in support_sets]
            for atom_id, support_sets in base.support_sets.items()
        },
        "essential_support": {
            atom_id: list(support)
            for atom_id, support in base.essential_support.items()
        },
    }


@dataclass(frozen=True)
class RevisionEpisodeSnapshot:
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
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

    @classmethod
    def from_episode(cls, episode: RevisionEpisode) -> RevisionEpisodeSnapshot:
        return cls(
            operator=episode.operator,
            input_atom_id=episode.input_atom_id,
            target_atom_ids=episode.target_atom_ids,
            accepted_atom_ids=episode.accepted_atom_ids,
            rejected_atom_ids=episode.rejected_atom_ids,
            incision_set=episode.incision_set,
            explanation=episode.explanation,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> RevisionEpisodeSnapshot:
        return cls(
            operator=str(data.get("operator") or ""),
            input_atom_id=None if data.get("input_atom_id") is None else str(data.get("input_atom_id")),
            target_atom_ids=tuple(str(atom_id) for atom_id in (data.get("target_atom_ids") or ())),
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (data.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (data.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            explanation={
                str(atom_id): RevisionAtomDetail.from_mapping(detail)
                for atom_id, detail in (data.get("explanation") or {}).items()
                if isinstance(detail, Mapping)
            },
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "operator": self.operator,
            "target_atom_ids": list(self.target_atom_ids),
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "rejected_atom_ids": list(self.rejected_atom_ids),
            "incision_set": list(self.incision_set),
            "explanation": {
                atom_id: detail.to_dict()
                for atom_id, detail in self.explanation.items()
            },
        }
        if self.input_atom_id is not None:
            data["input_atom_id"] = self.input_atom_id
        return data


@dataclass(frozen=True)
class EpistemicStateSnapshot:
    scope: RevisionScope
    base: BeliefBase
    accepted_atom_ids: tuple[str, ...]
    ranked_atom_ids: tuple[str, ...]
    ranking: Mapping[str, int] = field(default_factory=dict)
    entrenchment_reasons: Mapping[str, EntrenchmentReason] = field(default_factory=dict)
    history: tuple[RevisionEpisodeSnapshot, ...] = ()

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

    @classmethod
    def from_state(cls, state: EpistemicState) -> EpistemicStateSnapshot:
        return cls(
            scope=state.scope,
            base=state.base,
            accepted_atom_ids=state.accepted_atom_ids,
            ranked_atom_ids=state.ranked_atom_ids,
            ranking=state.ranking,
            entrenchment_reasons=state.entrenchment_reasons,
            history=tuple(RevisionEpisodeSnapshot.from_episode(episode) for episode in state.history),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EpistemicStateSnapshot:
        return cls(
            scope=_scope_from_mapping(_required_mapping(data.get("scope"), "scope")),
            base=_belief_base_from_mapping(_required_mapping(data.get("base"), "base")),
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (data.get("accepted_atom_ids") or ())),
            ranked_atom_ids=tuple(str(atom_id) for atom_id in (data.get("ranked_atom_ids") or ())),
            ranking={
                str(atom_id): int(rank)
                for atom_id, rank in (data.get("ranking") or {}).items()
            },
            entrenchment_reasons={
                str(atom_id): EntrenchmentReason.from_mapping(reason)
                for atom_id, reason in (data.get("entrenchment_reasons") or {}).items()
                if isinstance(reason, Mapping)
            },
            history=tuple(
                RevisionEpisodeSnapshot.from_mapping(item)
                for item in (data.get("history") or ())
                if isinstance(item, Mapping)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": _scope_to_dict(self.scope),
            "base": _belief_base_to_dict(self.base),
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "ranked_atom_ids": list(self.ranked_atom_ids),
            "ranking": dict(self.ranking),
            "entrenchment_reasons": {
                atom_id: reason.to_dict()
                for atom_id, reason in self.entrenchment_reasons.items()
            },
            "history": [episode.to_dict() for episode in self.history],
        }


def epistemic_state_snapshot(state: EpistemicState) -> EpistemicStateSnapshot:
    return EpistemicStateSnapshot.from_state(state)
