from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from propstore.cel_types import to_cel_expr
from propstore.core.assertions.codec import AssertionCanonicalRecord
from propstore.core.id_types import (
    AssumptionId,
    ContextId,
)
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
    AssertionAtom,
    RevisionEvent,
    RevisionEpisode,
    RevisionScope,
)


def _environment_key_to_dict(environment: EnvironmentKey) -> dict[str, Any]:
    return {
        "assumption_ids": list(environment.assumption_ids),
    }


def _label_to_dict(label: Label | None) -> dict[str, Any] | None:
    if label is None:
        return None
    return {
        "environments": [
            _environment_key_to_dict(environment) for environment in label.environments
        ]
    }


def _assumption_ref_to_dict(assumption: AssumptionRef) -> dict[str, Any]:
    return {
        "assumption_id": assumption.assumption_id,
        "kind": assumption.kind,
        "source": assumption.source,
        "cel": assumption.cel,
    }


def _required_mapping(data: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ValueError(f"Support revision snapshot requires mapping '{field_name}'")
    return data


def _optional_mapping(data: object, field_name: str) -> Mapping[str, Any]:
    if data is None:
        return {}
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


def _belief_atom_to_dict(atom: BeliefAtom) -> dict[str, Any]:
    if isinstance(atom, AssertionAtom):
        payload = {
            "assertion": AssertionCanonicalRecord.from_assertion(
                atom.assertion
            ).to_payload(),
            "source_claim_ids": list(atom.source_claim_ids),
        }
        kind = "assertion"
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


def belief_atom_from_canonical_dict(data: Mapping[str, Any]) -> BeliefAtom:
    return _belief_atom_from_json_payload(data)


def belief_atom_to_canonical_dict(atom: BeliefAtom) -> dict[str, Any]:
    return _belief_atom_to_dict(atom)


def _belief_base_to_dict(base: BeliefBase) -> dict[str, Any]:
    return {
        "scope": _scope_to_dict(base.scope),
        "atoms": [_belief_atom_to_dict(atom) for atom in base.atoms],
        "assumptions": [
            _assumption_ref_to_dict(assumption) for assumption in base.assumptions
        ],
        "support_sets": {
            atom_id: [list(support_set) for support_set in support_sets]
            for atom_id, support_sets in base.support_sets.items()
        },
        "essential_support": {
            atom_id: list(support)
            for atom_id, support in base.essential_support.items()
        },
    }


def belief_base_to_canonical_dict(base: BeliefBase) -> dict[str, Any]:
    return _belief_base_to_dict(base)


@dataclass(frozen=True)
class RevisionEpisodeSnapshot:
    operator: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)
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
            event=episode.event,
        )

    def to_episode(self) -> RevisionEpisode:
        return RevisionEpisode(
            operator=self.operator,
            input_atom_id=self.input_atom_id,
            target_atom_ids=self.target_atom_ids,
            accepted_atom_ids=self.accepted_atom_ids,
            rejected_atom_ids=self.rejected_atom_ids,
            incision_set=self.incision_set,
            explanation=self.explanation,
            event=self.event,
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
        if self.event is not None:
            data["event"] = self.event.to_dict()
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
                str(atom_id): coerce_entrenchment_reason(reason)
                for atom_id, reason in self.entrenchment_reasons.items()
            },
        )
        object.__setattr__(self, "history", tuple(self.history))

    @classmethod
    def from_state(cls, state: EpistemicState) -> EpistemicStateSnapshot:
        snapshot = cls(
            scope=state.scope,
            base=state.base,
            accepted_atom_ids=state.accepted_atom_ids,
            ranked_atom_ids=state.ranked_atom_ids,
            ranking=state.ranking,
            entrenchment_reasons=state.entrenchment_reasons,
            history=tuple(
                RevisionEpisodeSnapshot.from_episode(episode)
                for episode in state.history
            ),
        )
        return cls.from_json_payload(snapshot.to_dict())

    def to_state(self) -> EpistemicState:
        return EpistemicState(
            scope=self.scope,
            base=self.base,
            accepted_atom_ids=self.accepted_atom_ids,
            ranked_atom_ids=self.ranked_atom_ids,
            ranking=dict(self.ranking),
            entrenchment_reasons=dict(self.entrenchment_reasons),
            history=tuple(episode.to_episode() for episode in self.history),
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
