from __future__ import annotations

import msgspec
from quire.documents import convert_document_value, to_document_builtins

from propstore.support_revision.explanation_types import (
    EntrenchmentReason,
    RevisionAtomDetail,
    coerce_entrenchment_reason,
    coerce_revision_atom_detail,
)
from propstore.support_revision.state import (
    BeliefBase,
    EpistemicState,
    RevisionEpisode,
    RevisionEvent,
    RevisionScope,
)


class RevisionEpisodeSnapshot(
    msgspec.Struct,
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
        self.target_atom_ids = tuple(str(atom_id) for atom_id in self.target_atom_ids)
        self.accepted_atom_ids = tuple(
            str(atom_id) for atom_id in self.accepted_atom_ids
        )
        self.rejected_atom_ids = tuple(
            str(atom_id) for atom_id in self.rejected_atom_ids
        )
        self.incision_set = tuple(str(atom_id) for atom_id in self.incision_set)
        self.explanation = {
            str(atom_id): coerce_revision_atom_detail(detail)
            for atom_id, detail in self.explanation.items()
        }

    @classmethod
    def from_episode(cls, episode: RevisionEpisode) -> RevisionEpisodeSnapshot:
        return cls(
            operator=episode.operator,
            input_atom_id=episode.input_atom_id,
            target_atom_ids=episode.target_atom_ids,
            accepted_atom_ids=episode.accepted_atom_ids,
            rejected_atom_ids=episode.rejected_atom_ids,
            incision_set=episode.incision_set,
            explanation=dict(episode.explanation),
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


class EpistemicStateSnapshot(
    msgspec.Struct,
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
    history: tuple[RevisionEpisodeSnapshot, ...] = ()

    def __post_init__(self) -> None:
        self.accepted_atom_ids = tuple(
            str(atom_id) for atom_id in self.accepted_atom_ids
        )
        self.ranked_atom_ids = tuple(str(atom_id) for atom_id in self.ranked_atom_ids)
        self.ranking = {
            str(atom_id): int(rank) for atom_id, rank in self.ranking.items()
        }
        self.entrenchment_reasons = {
            str(atom_id): coerce_entrenchment_reason(reason)
            for atom_id, reason in self.entrenchment_reasons.items()
        }
        self.history = tuple(self.history)

    @classmethod
    def from_state(cls, state: EpistemicState) -> EpistemicStateSnapshot:
        snapshot = cls(
            scope=state.scope,
            base=state.base,
            accepted_atom_ids=state.accepted_atom_ids,
            ranked_atom_ids=state.ranked_atom_ids,
            ranking=dict(state.ranking),
            entrenchment_reasons=dict(state.entrenchment_reasons),
            history=tuple(
                RevisionEpisodeSnapshot.from_episode(episode)
                for episode in state.history
            ),
        )
        return convert_document_value(
            to_document_builtins(snapshot),
            cls,
            source="epistemic state snapshot",
        )

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
