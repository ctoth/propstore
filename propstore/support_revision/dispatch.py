from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from propstore.support_revision.belief_set_adapter import (
    DEFAULT_MAX_ALPHABET_SIZE,
    decide_contract,
    decide_expand,
    decide_revise,
)
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.iterated import advance_epistemic_state, iterated_revise
from propstore.support_revision.realization import realize_formal_decision
from propstore.support_revision.snapshot_types import (
    EpistemicStateSnapshot,
    belief_atom_from_canonical_dict,
)
from propstore.support_revision.state import (
    BeliefAtom,
    EpistemicState,
    RevisionEvent,
    RevisionRealizationFailure,
)


def dispatch(
    operator: JournalOperator,
    *,
    state_in: Mapping[str, Any],
    operator_input: Mapping[str, Any],
    policy: Mapping[str, str],
) -> EpistemicState:
    """Replay one support-revision journal operator from normalized inputs."""

    op = JournalOperator(operator)
    state = EpistemicStateSnapshot.from_mapping(state_in).to_state()
    payload = _required_mapping(operator_input, "operator_input")
    _required_policy_snapshot(policy)
    policy_snapshot = {str(key): str(value) for key, value in policy.items()}

    if op is JournalOperator.ITERATED_REVISE:
        atom = _formula_atom(payload)
        targets = _string_tuple(payload.get("targets") or ())
        revision_operator = str(payload.get("revision_operator") or "")
        conflicts: dict[str, tuple[str, ...] | list[str]] | None = (
            {atom.atom_id: targets} if targets else None
        )
        _, next_state = iterated_revise(
            state,
            atom,
            max_candidates=_max_candidates(payload),
            conflicts=conflicts,
            operator=revision_operator,
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )
        return next_state

    entrenchment = _entrenchment_from_state(state)
    if op is JournalOperator.EXPAND:
        atom = _formula_atom(payload)
        decision = decide_expand(
            state.base,
            atom,
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        try:
            result = realize_formal_decision(
                state.base,
                decision,
                extra_atoms=(atom,),
                accepted_reason="expanded",
            )
        except Exception as exc:
            _raise_realization_failure(
                state,
                operation=op.value,
                input_atom_id=atom.atom_id,
                target_atom_ids=(),
                decision_report=decision.report,
                policy_snapshot=policy_snapshot,
                exc=exc,
            )
        return advance_epistemic_state(
            state,
            result,
            entrenchment,
            operator=op.value,
            input_atom_id=atom.atom_id,
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )

    if op is JournalOperator.REVISE:
        atom = _formula_atom(payload)
        conflicts_payload = payload.get("conflicts") or {}
        conflicts = {
            str(atom_id): _string_tuple(targets)
            for atom_id, targets in _required_mapping(conflicts_payload, "conflicts").items()
        }
        decision = decide_revise(
            state.base,
            atom,
            conflicts=tuple(conflicts.get(atom.atom_id, ())),
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        target_atom_ids = tuple(conflicts.get(atom.atom_id, ()))
        try:
            result = realize_formal_decision(
                state.base,
                decision,
                extra_atoms=(atom,),
                accepted_reason="revised_in",
                rejected_reason="revised_out",
                support_entrenchment=entrenchment,
                max_candidates=_max_candidates(payload),
            )
        except Exception as exc:
            _raise_realization_failure(
                state,
                operation=op.value,
                input_atom_id=atom.atom_id,
                target_atom_ids=target_atom_ids,
                decision_report=decision.report,
                policy_snapshot=policy_snapshot,
                exc=exc,
            )
        return advance_epistemic_state(
            state,
            result,
            entrenchment,
            operator=op.value,
            input_atom_id=atom.atom_id,
            target_atom_ids=target_atom_ids,
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )

    if op is JournalOperator.CONTRACT:
        targets = _string_tuple(payload.get("targets") or ())
        decision = decide_contract(
            state.base,
            targets,
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        try:
            result = realize_formal_decision(
                state.base,
                decision,
                rejected_reason="contracted",
                support_entrenchment=entrenchment,
                max_candidates=_max_candidates(payload),
            )
        except Exception as exc:
            _raise_realization_failure(
                state,
                operation=op.value,
                input_atom_id=None,
                target_atom_ids=targets,
                decision_report=decision.report,
                policy_snapshot=policy_snapshot,
                exc=exc,
            )
        return advance_epistemic_state(
            state,
            result,
            entrenchment,
            operator=op.value,
            target_atom_ids=targets,
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )

    raise ValueError(f"unsupported journal operator: {op.value}")


def _formula_atom(payload: Mapping[str, Any]) -> BeliefAtom:
    formula = payload.get("formula")
    if not isinstance(formula, Mapping):
        raise ValueError("journal operator_input.formula must be a normalized belief atom")
    return belief_atom_from_canonical_dict(formula)


def _entrenchment_from_state(state: EpistemicState) -> EntrenchmentReport:
    return EntrenchmentReport(
        ranked_atom_ids=tuple(state.ranked_atom_ids),
        reasons=dict(state.entrenchment_reasons),
    )


def _max_candidates(payload: Mapping[str, Any]) -> int:
    value = payload.get("max_candidates")
    if value is None:
        raise ValueError("journal operator_input.max_candidates is required")
    return int(value)


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
        raise ValueError(f"journal dispatch missing policy versions: {', '.join(missing)}")
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


def _string_tuple(value: Sequence[object]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)
