from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NoReturn

from quire.documents import convert_document_value

from propstore.support_revision.belief_set_adapter import (
    DEFAULT_MAX_ALPHABET_SIZE,
    decide_contract,
    decide_expand,
    decide_ic_merge_profile,
    decide_revise,
)
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.iterated import advance_epistemic_state, iterated_revise
from propstore.support_revision.realization import (
    realize_formal_decision,
    realize_ic_merge_decision,
)
from propstore.support_revision.decision_trace import ICMergeTrace
from propstore.support_revision.integrity_constraints import IntegrityConstraintSpec
from propstore.support_revision.operator_inputs import (
    ContractInput,
    ExpandInput,
    ICMergeInput,
    IteratedReviseInput,
    OperatorInput,
    ReviseInput,
)
from propstore.support_revision.state import (
    EpistemicState,
    FormalRevisionDecisionReport,
    RevisionEvent,
    RevisionMergeRequiredFailure,
    RevisionRealizationFailure,
)


def dispatch(
    operator: JournalOperator,
    *,
    state_in: Mapping[str, Any],
    operator_input: OperatorInput,
    policy: Mapping[str, str],
) -> EpistemicState:
    """Replay one support-revision journal operator from its typed input.

    The input is a tagged union, so the operator's arguments arrive already
    discriminated: a malformed or mismatched entry fails when the journal is
    decoded, not part-way through a replay.
    """

    op = JournalOperator(operator)
    expected = _OPERATOR_BY_INPUT[type(operator_input)]
    if op is not expected:
        raise ValueError(
            f"journal entry operator {op.value!r} does not match its input, "
            f"which is a {expected.value!r} input"
        )
    state = convert_document_value(
        state_in,
        EpistemicState,
        source="journal state_in",
    )
    _required_policy_snapshot(policy)
    policy_snapshot = {str(key): str(value) for key, value in policy.items()}

    if isinstance(operator_input, IteratedReviseInput):
        atom = operator_input.formula
        targets = operator_input.targets
        conflicts: dict[str, tuple[str, ...] | list[str]] | None = (
            {atom.atom_id: targets} if targets else None
        )
        _, next_state = iterated_revise(
            state,
            atom,
            max_candidates=operator_input.max_candidates,
            conflicts=conflicts,
            operator=operator_input.revision_operator,
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )
        return next_state

    if isinstance(operator_input, ICMergeInput):
        integrity_constraint = operator_input.integrity_constraint
        entrenchment = _entrenchment_from_state(state)
        profile_atom_ids = operator_input.profile_atom_ids
        decision = decide_ic_merge_profile(
            profile_atom_ids=profile_atom_ids,
            integrity_constraint=integrity_constraint,
            merge_operator=operator_input.merge_operator,
            max_alphabet_size=operator_input.max_alphabet_size,
        )
        try:
            result = realize_ic_merge_decision(state.base, decision)
        except RevisionMergeRequiredFailure as exc:
            _raise_ic_merge_failure(
                state,
                decision=decision.report,
                profile_atom_ids=profile_atom_ids,
                integrity_constraint=integrity_constraint,
                policy_snapshot=policy_snapshot,
                exc=exc,
            )
        return advance_epistemic_state(
            state,
            result,
            entrenchment,
            operator=op.value,
            target_atom_ids=tuple(decision.projection.formula_by_atom_id),
            policy_snapshot=policy_snapshot,
            replay_status="replayed",
        )

    entrenchment = _entrenchment_from_state(state)
    if isinstance(operator_input, ExpandInput):
        atom = operator_input.formula
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

    if isinstance(operator_input, ReviseInput):
        atom = operator_input.formula
        target_atom_ids = operator_input.targets_for(atom.atom_id)
        decision = decide_revise(
            state.base,
            atom,
            conflicts=target_atom_ids,
            max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
        )
        try:
            result = realize_formal_decision(
                state.base,
                decision,
                extra_atoms=(atom,),
                accepted_reason="revised_in",
                rejected_reason="revised_out",
                support_entrenchment=entrenchment,
                max_candidates=operator_input.max_candidates,
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

    # The union is exhausted: ContractInput is all that is left.
    targets = operator_input.targets
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
            max_candidates=operator_input.max_candidates,
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


_OPERATOR_BY_INPUT: dict[type[OperatorInput], JournalOperator] = {
    ExpandInput: JournalOperator.EXPAND,
    ContractInput: JournalOperator.CONTRACT,
    ReviseInput: JournalOperator.REVISE,
    IteratedReviseInput: JournalOperator.ITERATED_REVISE,
    ICMergeInput: JournalOperator.IC_MERGE,
}


def _entrenchment_from_state(state: EpistemicState) -> EntrenchmentReport:
    return EntrenchmentReport(
        ranked_atom_ids=tuple(state.ranked_atom_ids),
        reasons=dict(state.entrenchment_reasons),
    )




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
    decision_report: FormalRevisionDecisionReport | None,
    policy_snapshot: Mapping[str, str],
    exc: Exception,
) -> NoReturn:
    from propstore.support_revision.history import EpistemicSnapshot

    event = RevisionEvent(
        operation=operation,
        pre_state_hash=EpistemicSnapshot.from_state(state).content_hash,
        input_atom_id=input_atom_id,
        target_atom_ids=target_atom_ids,
        decision=decision_report,
        realization=None,
        policy_snapshot=dict(policy_snapshot),
        replay_status="realization_failed",
        realization_failure=str(exc),
    )
    raise RevisionRealizationFailure(event) from exc


def _raise_ic_merge_failure(
    state: EpistemicState,
    *,
    decision: FormalRevisionDecisionReport | None,
    profile_atom_ids: tuple[tuple[str, ...], ...],
    integrity_constraint: IntegrityConstraintSpec,
    policy_snapshot: Mapping[str, str],
    exc: RevisionMergeRequiredFailure,
) -> NoReturn:
    from propstore.support_revision.history import EpistemicSnapshot

    decision_report = exc.decision_report or decision
    selected_worlds_hash = exc.selected_worlds_hash
    if selected_worlds_hash is None and decision_report is not None:
        selected_worlds_hash = _selected_worlds_hash(decision_report)
    event = RevisionEvent(
        operation=JournalOperator.IC_MERGE.value,
        pre_state_hash=EpistemicSnapshot.from_state(state).content_hash,
        target_atom_ids=tuple(atom_id for profile in profile_atom_ids for atom_id in profile),
        decision=decision_report,
        realization=None,
        policy_snapshot=dict(policy_snapshot),
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





def _selected_worlds_hash(report: FormalRevisionDecisionReport | None) -> str | None:
    """The worlds an IC merge selected — only an IC merge selects any."""

    if report is None or not isinstance(report.trace, ICMergeTrace):
        return None
    return report.trace.selected_worlds_hash or None
