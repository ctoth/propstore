from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.state import (
    EpistemicState,
    RevisionEvent,
    RevisionMergeRequiredFailure,
    RevisionRealizationFailure,
)


def _entrenchment_from_state(state: EpistemicState) -> EntrenchmentReport:
    return EntrenchmentReport(
        ranked_atom_ids=tuple(state.ranked_atom_ids),
        reasons=dict(state.entrenchment_reasons),
    )


def _required_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"journal dispatch requires mapping '{field_name}'")
    return value


def _required_policy_snapshot(value: Mapping[str, str]) -> None:
    required = {
        "revision_policy_version",
        "ranking_policy_version",
        "entrenchment_policy_version",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(
            f"journal dispatch missing policy versions: {', '.join(missing)}"
        )
    empty = sorted(key for key in required if not str(value.get(key) or "").strip())
    if empty:
        raise ValueError(f"journal dispatch empty policy versions: {', '.join(empty)}")


def _raise_realization_failure(
    state: EpistemicState,
    *,
    operation: str,
    input_atom_id: str | None,
    target_atom_ids: tuple[str, ...],
    decision_report,
    policy_snapshot: Mapping[str, str],
    exc: Exception,
) -> None:
    from propstore.support_revision.history import EpistemicSnapshot

    event = RevisionEvent(
        operation=operation,
        pre_state_hash=EpistemicSnapshot.from_state(state).content_hash,
        input_atom_id=input_atom_id,
        target_atom_ids=target_atom_ids,
        decision=decision_report,
        realization=None,
        policy_snapshot=policy_snapshot,
        replay_status="realization_failed",
        realization_failure=str(exc),
    )
    raise RevisionRealizationFailure(event) from exc


def _raise_ic_merge_failure(
    state: EpistemicState,
    *,
    decision,
    profile_atom_ids: tuple[tuple[str, ...], ...],
    integrity_constraint: Mapping[str, Any],
    policy_snapshot: Mapping[str, str],
    exc: RevisionMergeRequiredFailure,
) -> None:
    from propstore.support_revision.history import EpistemicSnapshot

    decision_report = exc.decision_report or decision
    selected_worlds_hash = exc.selected_worlds_hash
    if selected_worlds_hash is None and decision_report is not None:
        selected_worlds_hash = decision_report.trace.get("selected_worlds_hash")
    event = RevisionEvent(
        operation=JournalOperator.IC_MERGE.value,
        pre_state_hash=EpistemicSnapshot.from_state(state).content_hash,
        target_atom_ids=tuple(
            atom_id for profile in profile_atom_ids for atom_id in profile
        ),
        decision=decision_report,
        realization=None,
        policy_snapshot=policy_snapshot,
        replay_status="realization_failed",
        realization_failure=exc.reason,
    )
    raise RevisionMergeRequiredFailure(
        reason=exc.reason,
        parent_commits=exc.parent_commits or state.scope.merge_parent_commits,
        decision_report=decision_report,
        profile_atom_ids=exc.profile_atom_ids or profile_atom_ids,
        integrity_constraint=exc.integrity_constraint or integrity_constraint,
        selected_worlds_hash=selected_worlds_hash,
        event=event,
    ) from exc


def _string_tuple(value: Sequence[object]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)


def _profile_atom_ids(value: Sequence[object]) -> tuple[tuple[str, ...], ...]:
    profiles: list[tuple[str, ...]] = []
    for profile in value:
        if isinstance(profile, str):
            raise ValueError("IC merge profile_atom_ids entries must be sequences")
        if not isinstance(profile, Sequence):
            raise ValueError("IC merge profile_atom_ids entries must be sequences")
        profiles.append(tuple(str(atom_id) for atom_id in profile))
    return tuple(profiles)
