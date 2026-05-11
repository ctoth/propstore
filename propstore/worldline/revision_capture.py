from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from propstore.support_revision.belief_set_adapter import DEFAULT_ITERATED_OPERATOR, DEFAULT_MAX_ALPHABET_SIZE
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.input_normalization import normalize_revision_input
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from propstore.support_revision.state import EpistemicState, RevisionEvent
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    WorldlineRevisionResult,
    WorldlineRevisionState,
)

_MAX_CANDIDATES = 1024
_POLICY_ID = "propstore-worldline-journal-v1"
_VERSION_POLICY_SNAPSHOT: Mapping[str, str] = {
    "revision_policy_version": "propstore-revision-v1",
    "ranking_policy_version": "propstore-ranking-v1",
    "entrenchment_policy_version": "propstore-entrenchment-v1",
}


def capture_revision_state(bound: Any, revision_query: Any) -> WorldlineRevisionState:
    operation = revision_query.operation
    if operation == "expand":
        result = bound.expand(_revision_atom_input(revision_query.atom))
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=(),
            result=_revision_result_payload(bound, result),
            event=_revision_event_payload(
                bound,
                operation=operation,
                input_atom_id=_query_atom_id(revision_query.atom),
                target_atom_ids=(),
                result=result,
            ),
        )
    if operation == "contract":
        result = bound.contract(revision_query.target, max_candidates=1024)
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=None,
            target_atom_ids=tuple(_query_target_atom_ids(revision_query.target)),
            result=_revision_result_payload(bound, result),
            event=_revision_event_payload(
                bound,
                operation=operation,
                input_atom_id=None,
                target_atom_ids=tuple(_query_target_atom_ids(revision_query.target)),
                result=result,
            ),
        )
    if operation == "revise":
        result = bound.revise(
            _revision_atom_input(revision_query.atom),
            conflicts=revision_query.conflicts.to_revision_input(),
            max_candidates=1024,
        )
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
            result=_revision_result_payload(bound, result),
            event=_revision_event_payload(
                bound,
                operation=operation,
                input_atom_id=_query_atom_id(revision_query.atom),
                target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
                result=result,
            ),
        )
    if operation == "iterated_revise":
        result, state = bound.iterated_revise(
            _revision_atom_input(revision_query.atom),
            conflicts=revision_query.conflicts.to_revision_input(),
            max_candidates=1024,
            operator=revision_query.operator or DEFAULT_ITERATED_OPERATOR,
        )
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
            result=_revision_result_payload(bound, result),
            state=_revision_state_snapshot(bound, state),
            event=_revision_event_payload(
                bound,
                operation=operation,
                input_atom_id=_query_atom_id(revision_query.atom),
                target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
                result=result,
            ),
        )
    raise ValueError(f"Unknown revision operation: {operation}")


def capture_journal(
    bound: Any,
    operations: Sequence[Any],
    *,
    policy_id: str = _POLICY_ID,
    policy_payload: Mapping[str, Any] | None = None,
) -> TransitionJournal:
    state = _initial_epistemic_state(bound)
    captured_policy_payload = {} if policy_payload is None else dict(policy_payload)
    entries: list[TransitionJournalEntry] = []
    for operation_query in operations:
        operator, operation, operator_input = _journal_operator_input(
            state,
            operation_query,
        )
        state_out = dispatch(
            operator,
            state_in=state.to_canonical_dict(),
            operator_input=operator_input,
            policy=_VERSION_POLICY_SNAPSHOT,
        )
        entries.append(
            TransitionJournalEntry.from_states(
                state_in=state,
                operation=operation,
                policy_id=policy_id,
                operator=operator,
                operator_input=operator_input,
                version_policy_snapshot=_VERSION_POLICY_SNAPSHOT,
                state_out=state_out,
                explanation={},
                policy_payload=captured_policy_payload,
            )
        )
        state = state_out
    return TransitionJournal(entries=tuple(entries))


def _revision_result_payload(bound: Any, result: Any) -> WorldlineRevisionResult:
    return WorldlineRevisionResult(
        accepted_atom_ids=tuple(result.accepted_atom_ids),
        rejected_atom_ids=tuple(result.rejected_atom_ids),
        incision_set=tuple(result.incision_set),
        explanation=bound.revision_explain(result),
    )


def _revision_event_payload(
    bound: Any,
    *,
    operation: str,
    input_atom_id: str | None,
    target_atom_ids: tuple[str, ...],
    result: Any,
) -> RevisionEvent:
    return RevisionEvent(
        operation=operation,
        pre_state_hash=_bound_epistemic_state_hash(bound),
        input_atom_id=input_atom_id,
        target_atom_ids=target_atom_ids,
        decision=getattr(result, "decision", None),
        realization=getattr(result, "realization", None),
        policy_snapshot=_VERSION_POLICY_SNAPSHOT,
        replay_status="captured",
    )


def _bound_epistemic_state_hash(bound: Any) -> str:
    state = getattr(bound, "epistemic_state", None)
    if not callable(state):
        return ""
    result = state()
    if not isinstance(result, EpistemicState):
        return ""
    from propstore.support_revision.history import EpistemicSnapshot

    return EpistemicSnapshot.from_state(result).content_hash


def _revision_atom_input(atom: RevisionAtomRef | None) -> Mapping[str, Any] | None:
    if atom is None:
        return None
    return atom.to_revision_input()


def _revision_state_snapshot(bound: Any, state: Any) -> Any:
    snapshot = getattr(bound, "revision_state_snapshot", None)
    if callable(snapshot):
        return snapshot(state)
    raise TypeError("revision capture requires bound.revision_state_snapshot(state)")


def _initial_epistemic_state(bound: Any) -> EpistemicState:
    state = getattr(bound, "epistemic_state", None)
    if not callable(state):
        raise TypeError("journal capture requires bound.epistemic_state()")
    result = state()
    if not isinstance(result, EpistemicState):
        raise TypeError("bound.epistemic_state() must return EpistemicState")
    return result


def _journal_operator_input(
    state: EpistemicState,
    revision_query: Any,
) -> tuple[JournalOperator, TransitionOperation, Mapping[str, Any]]:
    operation = str(revision_query.operation)
    if operation == "expand":
        atom = _normalize_query_atom(state, revision_query.atom)
        return (
            JournalOperator.EXPAND,
            TransitionOperation(
                name=operation,
                input_atom_id=atom.atom_id,
                target_atom_ids=(),
            ),
            {
                "formula": belief_atom_to_canonical_dict(atom),
                "max_candidates": _MAX_CANDIDATES,
                "conflicts": {},
            },
        )
    if operation == "contract":
        targets = tuple(_query_target_atom_ids(revision_query.target))
        return (
            JournalOperator.CONTRACT,
            TransitionOperation(
                name=operation,
                input_atom_id=None,
                target_atom_ids=targets,
            ),
            {
                "targets": targets,
                "max_candidates": _MAX_CANDIDATES,
            },
        )
    if operation == "revise":
        atom = _normalize_query_atom(state, revision_query.atom)
        conflicts = revision_query.conflicts.to_revision_input()
        return (
            JournalOperator.REVISE,
            TransitionOperation(
                name=operation,
                input_atom_id=atom.atom_id,
                target_atom_ids=tuple(conflicts.get(atom.atom_id, ())),
            ),
            {
                "formula": belief_atom_to_canonical_dict(atom),
                "max_candidates": _MAX_CANDIDATES,
                "conflicts": conflicts,
            },
        )
    if operation == "iterated_revise":
        atom = _normalize_query_atom(state, revision_query.atom)
        targets = tuple(revision_query.conflicts.targets_for(atom.atom_id))
        operator = revision_query.operator or DEFAULT_ITERATED_OPERATOR
        return (
            JournalOperator.ITERATED_REVISE,
            TransitionOperation(
                name=operation,
                input_atom_id=atom.atom_id,
                target_atom_ids=targets,
                parameters={"operator": operator},
            ),
            {
                "formula": belief_atom_to_canonical_dict(atom),
                "targets": targets,
                "revision_operator": operator,
                "max_candidates": _MAX_CANDIDATES,
            },
        )
    if operation == "ic_merge":
        profile_atom_ids = tuple(tuple(str(atom_id) for atom_id in profile) for profile in revision_query.profile_atom_ids)
        if not profile_atom_ids:
            raise ValueError("IC merge journal capture requires profile_atom_ids")
        integrity_constraint = revision_query.integrity_constraint
        if not isinstance(integrity_constraint, Mapping):
            raise ValueError("IC merge journal capture requires integrity_constraint")
        merge_parent_commits = tuple(revision_query.merge_parent_commits or state.scope.merge_parent_commits)
        merge_operator = revision_query.operator or "sigma"
        max_alphabet_size = revision_query.max_alphabet_size or DEFAULT_MAX_ALPHABET_SIZE
        target_atom_ids = tuple(dict.fromkeys(atom_id for profile in profile_atom_ids for atom_id in profile))
        operator_input = {
            "profile_atom_ids": profile_atom_ids,
            "merge_parent_commits": merge_parent_commits,
            "integrity_constraint": dict(integrity_constraint),
            "merge_operator": merge_operator,
            "max_alphabet_size": max_alphabet_size,
        }
        return (
            JournalOperator.IC_MERGE,
            TransitionOperation(
                name=operation,
                input_atom_id=None,
                target_atom_ids=target_atom_ids,
                parameters=operator_input,
            ),
            operator_input,
        )
    raise ValueError(f"Unknown revision operation: {operation}")


def _normalize_query_atom(state: EpistemicState, atom: RevisionAtomRef | None):
    if atom is None:
        raise ValueError("journal revision operation requires an atom")
    return normalize_revision_input(state.base, atom.to_revision_input())


def _query_atom_id(atom: RevisionAtomRef | None) -> str | None:
    if atom is None:
        return None
    return atom.resolved_atom_id()


def _query_target_atom_ids(target: Any) -> list[str]:
    if target is None:
        return []
    if isinstance(target, str):
        if target.startswith("ps:assertion:") or target.startswith("assumption:"):
            return [target]
        raise ValueError(f"Worldline revision target must be an assertion or assumption atom id: {target}")
    return [str(target)]


def _query_conflict_target_atom_ids(revision_query: Any) -> list[str]:
    input_atom_id = _query_atom_id(revision_query.atom)
    if input_atom_id is None:
        return []
    targets = revision_query.conflicts.targets_for(input_atom_id)
    invalid = [
        target
        for target in targets
        if not (target.startswith("ps:assertion:") or target.startswith("assumption:"))
    ]
    if invalid:
        raise ValueError(
            "Worldline revision conflicts must name assertion or assumption atom ids: "
            + ", ".join(invalid)
        )
    return list(targets)
