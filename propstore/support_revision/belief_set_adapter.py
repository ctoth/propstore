from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from belief_set import (
    AlphabetBudgetExceeded,
    Atom,
    BeliefSet,
    EnumerationExceeded,
    EpistemicEntrenchment,
    Formula,
    ICMergeOutcome,
    RevisionOutcome,
    SpohnEpistemicState,
    expand,
    full_meet_contract,
    lexicographic_revise,
    merge_belief_profile,
    restrained_revise,
    revise,
    conjunction,
    negate,
)

from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    FormalRevisionDecisionReport,
)


LEXICOGRAPHIC_OPERATOR = "lexicographic"
RESTRAINED_OPERATOR = "restrained"
DEFAULT_ITERATED_OPERATOR = RESTRAINED_OPERATOR


@dataclass(frozen=True)
class FormalProjectionBundle:
    alphabet: frozenset[str]
    belief_set: BeliefSet
    formula_by_atom_id: Mapping[str, Formula] = field(default_factory=dict)
    atom_id_by_formula_name: Mapping[str, str] = field(default_factory=dict)
    epistemic_state: SpohnEpistemicState | None = None
    entrenchment: EpistemicEntrenchment | None = None
    budget_config: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class FormalDecision:
    projection: FormalProjectionBundle
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState
    operation: str
    report: FormalRevisionDecisionReport


def is_formal_budget_error(exc: BaseException) -> bool:
    return isinstance(exc, AlphabetBudgetExceeded | EnumerationExceeded)


def project_formal_bundle(
    base: BeliefBase,
    *,
    extra_atoms: tuple[BeliefAtom, ...] = (),
    max_alphabet_size: int = 16,
) -> FormalProjectionBundle:
    atoms_by_id = {atom.atom_id: atom for atom in base.atoms}
    for atom in extra_atoms:
        atoms_by_id.setdefault(atom.atom_id, atom)
    alphabet = frozenset(atoms_by_id)
    if len(alphabet) > max_alphabet_size:
        raise AlphabetBudgetExceeded(
            alphabet_size=len(alphabet),
            max_alphabet_size=max_alphabet_size,
        )
    formula_by_atom_id = {
        atom_id: Atom(_formula_name(atom_id))
        for atom_id in sorted(atoms_by_id)
    }
    base_formulas = tuple(
        formula_by_atom_id[atom.atom_id]
        for atom in base.atoms
        if atom.atom_id in formula_by_atom_id
    )
    belief_set = BeliefSet.from_formula(
        alphabet,
        conjunction(*base_formulas),
    )
    epistemic_state = _distance_ranked_state(belief_set)
    return FormalProjectionBundle(
        alphabet=alphabet,
        belief_set=belief_set,
        formula_by_atom_id=formula_by_atom_id,
        atom_id_by_formula_name={
            _formula_name(atom_id): atom_id
            for atom_id in formula_by_atom_id
        },
        epistemic_state=epistemic_state,
        entrenchment=EpistemicEntrenchment.from_state(epistemic_state),
        budget_config={"max_alphabet_size": max_alphabet_size},
    )


def decide_expand(
    base: BeliefBase,
    atom: BeliefAtom,
    *,
    max_alphabet_size: int,
) -> FormalDecision:
    bundle = project_formal_bundle(base, extra_atoms=(atom,), max_alphabet_size=max_alphabet_size)
    formula = bundle.formula_by_atom_id[atom.atom_id]
    outcome = expand(bundle.belief_set, formula)
    report = _decision_report(
        operation="expand",
        policy="belief_set.expand",
        bundle=bundle,
        outcome=outcome,
        input_formula_ids=(atom.atom_id,),
    )
    return FormalDecision(bundle, outcome, "expand", report)


def decide_contract(
    base: BeliefBase,
    target_atom_ids: tuple[str, ...],
    *,
    max_alphabet_size: int,
) -> FormalDecision:
    bundle = project_formal_bundle(base, max_alphabet_size=max_alphabet_size)
    formula = conjunction(*(bundle.formula_by_atom_id[atom_id] for atom_id in target_atom_ids))
    outcome = full_meet_contract(
        _state_for(bundle),
        formula,
        max_alphabet_size=max_alphabet_size,
    )
    report = _decision_report(
        operation="contract",
        policy="belief_set.agm.full_meet_contract",
        bundle=bundle,
        outcome=outcome,
        input_formula_ids=target_atom_ids,
    )
    return FormalDecision(bundle, outcome, "contract", report)


def decide_revise(
    base: BeliefBase,
    atom: BeliefAtom,
    *,
    conflicts: tuple[str, ...] = (),
    max_alphabet_size: int,
) -> FormalDecision:
    bundle = project_formal_bundle(base, extra_atoms=(atom,), max_alphabet_size=max_alphabet_size)
    formula = _revision_formula(
        bundle,
        atom.atom_id,
        conflicts,
        base_atom_ids=tuple(base_atom.atom_id for base_atom in base.atoms),
    )
    outcome = revise(
        _state_for(bundle),
        formula,
        max_alphabet_size=max_alphabet_size,
    )
    report = _decision_report(
        operation="revise",
        policy="belief_set.agm.revise",
        bundle=bundle,
        outcome=outcome,
        input_formula_ids=_input_formula_ids(atom.atom_id, conflicts),
    )
    return FormalDecision(bundle, outcome, "revise", report)


def decide_iterated_revise(
    base: BeliefBase,
    atom: BeliefAtom,
    *,
    conflicts: tuple[str, ...] = (),
    operator: str,
    max_alphabet_size: int,
) -> FormalDecision:
    bundle = project_formal_bundle(base, extra_atoms=(atom,), max_alphabet_size=max_alphabet_size)
    formula = _revision_formula(
        bundle,
        atom.atom_id,
        conflicts,
        base_atom_ids=tuple(base_atom.atom_id for base_atom in base.atoms),
    )
    operators = {
        LEXICOGRAPHIC_OPERATOR: lexicographic_revise,
        RESTRAINED_OPERATOR: restrained_revise,
    }
    try:
        revise_operator = operators[operator]
    except KeyError as exc:
        raise ValueError(f"Unsupported iterated revision operator: {operator}") from exc
    outcome = revise_operator(
        _state_for(bundle),
        formula,
        max_alphabet_size=max_alphabet_size,
    )
    report = _decision_report(
        operation="iterated_revise",
        policy=f"belief_set.iterated.{operator}",
        bundle=bundle,
        outcome=outcome,
        input_formula_ids=_input_formula_ids(atom.atom_id, conflicts),
    )
    return FormalDecision(bundle, outcome, "iterated_revise", report)


def accepted_atom_ids(decision: FormalDecision) -> tuple[str, ...]:
    belief_set = _outcome_belief_set(decision.outcome)
    return tuple(
        atom_id
        for atom_id, formula in decision.projection.formula_by_atom_id.items()
        if belief_set.entails(formula)
    )


def rejected_atom_ids(decision: FormalDecision) -> tuple[str, ...]:
    accepted = set(accepted_atom_ids(decision))
    return tuple(
        atom_id
        for atom_id in decision.projection.formula_by_atom_id
        if atom_id not in accepted
    )


def _decision_report(
    *,
    operation: str,
    policy: str,
    bundle: FormalProjectionBundle,
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState,
    input_formula_ids: tuple[str, ...],
) -> FormalRevisionDecisionReport:
    belief_set = _outcome_belief_set(outcome)
    accepted = tuple(
        atom_id
        for atom_id, formula in bundle.formula_by_atom_id.items()
        if belief_set.entails(formula)
    )
    rejected = tuple(
        atom_id
        for atom_id in bundle.formula_by_atom_id
        if atom_id not in set(accepted)
    )
    state = _outcome_state(outcome)
    return FormalRevisionDecisionReport(
        operation=operation,
        policy=policy,
        input_formula_ids=input_formula_ids,
        accepted_formula_ids=accepted,
        rejected_formula_ids=rejected,
        epistemic_state_hash=None if state is None else _state_hash(state),
        trace=_trace_payload(outcome),
    )


def _revision_formula(
    bundle: FormalProjectionBundle,
    atom_id: str,
    conflicts: tuple[str, ...],
    *,
    base_atom_ids: tuple[str, ...],
) -> Formula:
    conflict_set = set(conflicts)
    formulas: list[Formula] = [
        bundle.formula_by_atom_id[base_atom_id]
        for base_atom_id in base_atom_ids
        if base_atom_id in bundle.formula_by_atom_id
        and base_atom_id not in conflict_set
        and base_atom_id != atom_id
    ]
    formulas.append(bundle.formula_by_atom_id[atom_id])
    formulas.extend(
        negate(bundle.formula_by_atom_id[conflict])
        for conflict in conflicts
        if conflict in bundle.formula_by_atom_id
    )
    return conjunction(*formulas)


def _input_formula_ids(atom_id: str, conflicts: tuple[str, ...]) -> tuple[str, ...]:
    return (atom_id,) + tuple(f"not:{conflict}" for conflict in conflicts)


def _outcome_belief_set(
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState,
) -> BeliefSet:
    if isinstance(outcome, BeliefSet):
        return outcome
    if isinstance(outcome, SpohnEpistemicState):
        return outcome.belief_set
    return outcome.belief_set


def _outcome_state(
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState,
) -> SpohnEpistemicState | None:
    if isinstance(outcome, RevisionOutcome):
        return outcome.state
    if isinstance(outcome, SpohnEpistemicState):
        return outcome
    return None


def _trace_payload(
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState,
) -> Mapping[str, Any]:
    if not isinstance(outcome, RevisionOutcome):
        return {}
    return {
        "operator": outcome.trace.operator,
        "pre_image_fingerprint": outcome.trace.pre_image_fingerprint,
        "timestamp": outcome.trace.timestamp.isoformat(),
    }


def _state_for(bundle: FormalProjectionBundle) -> SpohnEpistemicState:
    if bundle.epistemic_state is None:
        return _distance_ranked_state(bundle.belief_set)
    return bundle.epistemic_state


def _distance_ranked_state(belief_set: BeliefSet) -> SpohnEpistemicState:
    if not belief_set.models:
        return SpohnEpistemicState.from_belief_set(belief_set)
    worlds = BeliefSet.all_worlds(belief_set.alphabet)
    return SpohnEpistemicState.from_ranks(
        belief_set.alphabet,
        {
            world: min(_hamming_distance(world, model) for model in belief_set.models)
            for world in worlds
        },
    )


def _hamming_distance(left: frozenset[str], right: frozenset[str]) -> int:
    return len(left.symmetric_difference(right))


def _state_hash(state: SpohnEpistemicState) -> str:
    payload = {
        "alphabet": sorted(state.alphabet),
        "ranks": [
            [sorted(world), _json_rank(rank)]
            for world, rank in sorted(state.ranks.items(), key=lambda item: tuple(sorted(item[0])))
        ],
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _json_rank(rank: int | float) -> int | float | str:
    rank_value = float(rank)
    if math.isinf(rank_value):
        return "inf"
    if math.isnan(rank_value):
        return "nan"
    return rank


def _formula_name(atom_id: str) -> str:
    return str(atom_id)


__all__ = [
    "FormalDecision",
    "FormalProjectionBundle",
    "DEFAULT_ITERATED_OPERATOR",
    "LEXICOGRAPHIC_OPERATOR",
    "RESTRAINED_OPERATOR",
    "accepted_atom_ids",
    "decide_contract",
    "decide_expand",
    "decide_iterated_revise",
    "decide_revise",
    "expand",
    "full_meet_contract",
    "is_formal_budget_error",
    "lexicographic_revise",
    "merge_belief_profile",
    "project_formal_bundle",
    "rejected_atom_ids",
    "restrained_revise",
    "revise",
]
