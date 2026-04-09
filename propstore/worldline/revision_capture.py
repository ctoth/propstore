from __future__ import annotations

from typing import Any


def capture_revision_state(bound: Any, revision_query: Any) -> dict[str, Any]:
    from propstore.revision.iterated import epistemic_state_payload

    operation = revision_query.operation
    if operation == "expand":
        result = bound.expand(revision_query.atom)
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": [],
            "result": _revision_result_payload(result),
        }
    if operation == "contract":
        result = bound.contract(revision_query.target)
        return {
            "operation": operation,
            "input_atom_id": None,
            "target_atom_ids": _query_target_atom_ids(revision_query.target),
            "result": _revision_result_payload(result),
        }
    if operation == "revise":
        result = bound.revise(revision_query.atom, conflicts=revision_query.conflicts)
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": _query_conflict_target_atom_ids(revision_query),
            "result": _revision_result_payload(result),
        }
    if operation == "iterated_revise":
        result, state = bound.iterated_revise(
            revision_query.atom,
            conflicts=revision_query.conflicts,
            operator=revision_query.operator or "restrained",
        )
        return {
            "operation": operation,
            "input_atom_id": _query_atom_id(revision_query.atom),
            "target_atom_ids": _query_conflict_target_atom_ids(revision_query),
            "result": _revision_result_payload(result),
            "state": epistemic_state_payload(state),
        }
    raise ValueError(f"Unknown revision operation: {operation}")


def _revision_result_payload(result: Any) -> dict[str, Any]:
    return {
        "accepted_atom_ids": list(result.accepted_atom_ids),
        "rejected_atom_ids": list(result.rejected_atom_ids),
        "incision_set": list(result.incision_set),
        "explanation": dict(result.explanation),
    }


def _query_atom_id(atom: dict[str, Any] | None) -> str | None:
    if not atom:
        return None
    kind = str(atom.get("kind") or "claim")
    if kind == "claim":
        claim_id = atom.get("id") or atom.get("claim_id")
        if claim_id:
            return f"claim:{claim_id}"
    if kind == "assumption":
        assumption_id = atom.get("assumption_id") or atom.get("id")
        if assumption_id:
            return f"assumption:{assumption_id}"
    atom_id = atom.get("atom_id")
    return str(atom_id) if atom_id else None


def _query_target_atom_ids(target: Any) -> list[str]:
    if target is None:
        return []
    if isinstance(target, str):
        if ":" in target:
            return [target]
        return [f"claim:{target}"]
    return [str(target)]


def _query_conflict_target_atom_ids(revision_query: Any) -> list[str]:
    input_atom_id = _query_atom_id(revision_query.atom)
    if input_atom_id is None:
        return []
    targets = revision_query.conflicts.get(input_atom_id, ())
    return [
        target if ":" in target else f"claim:{target}"
        for target in targets
    ]
