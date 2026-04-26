from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.worldline.revision_types import (
    RevisionAtomRef,
    WorldlineRevisionResult,
    WorldlineRevisionState,
)

def capture_revision_state(bound: Any, revision_query: Any) -> WorldlineRevisionState:
    operation = revision_query.operation
    if operation == "expand":
        result = bound.expand(_revision_atom_input(revision_query.atom))
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=(),
            result=_revision_result_payload(bound, result),
        )
    if operation == "contract":
        result = bound.contract(revision_query.target)
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=None,
            target_atom_ids=tuple(_query_target_atom_ids(revision_query.target)),
            result=_revision_result_payload(bound, result),
        )
    if operation == "revise":
        result = bound.revise(
            _revision_atom_input(revision_query.atom),
            conflicts=revision_query.conflicts.to_revision_input(),
        )
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
            result=_revision_result_payload(bound, result),
        )
    if operation == "iterated_revise":
        result, state = bound.iterated_revise(
            _revision_atom_input(revision_query.atom),
            conflicts=revision_query.conflicts.to_revision_input(),
            operator=revision_query.operator or "restrained",
        )
        return WorldlineRevisionState(
            operation=operation,
            input_atom_id=_query_atom_id(revision_query.atom),
            target_atom_ids=tuple(_query_conflict_target_atom_ids(revision_query)),
            result=_revision_result_payload(bound, result),
            state=_revision_state_snapshot(bound, state),
        )
    raise ValueError(f"Unknown revision operation: {operation}")


def _revision_result_payload(bound: Any, result: Any) -> WorldlineRevisionResult:
    return WorldlineRevisionResult(
        accepted_atom_ids=tuple(result.accepted_atom_ids),
        rejected_atom_ids=tuple(result.rejected_atom_ids),
        incision_set=tuple(result.incision_set),
        explanation=bound.revision_explain(result),
    )


def _revision_atom_input(atom: RevisionAtomRef | None) -> Mapping[str, Any] | None:
    if atom is None:
        return None
    return atom.to_revision_input()


def _revision_state_snapshot(bound: Any, state: Any) -> Any:
    snapshot = getattr(bound, "revision_state_snapshot", None)
    if callable(snapshot):
        return snapshot(state)
    to_dict = getattr(state, "to_dict", None)
    if callable(to_dict):
        return state
    raise TypeError("revision capture requires bound.revision_state_snapshot(state)")


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
