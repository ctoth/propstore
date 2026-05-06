from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from belief_set import (
    AlphabetBudgetExceeded,
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
)


@dataclass(frozen=True)
class FormalProjectionBundle:
    alphabet: frozenset[str]
    belief_set: BeliefSet
    formula_by_atom_id: Mapping[str, Formula] = field(default_factory=dict)
    atom_id_by_formula_name: Mapping[str, str] = field(default_factory=dict)
    epistemic_state: SpohnEpistemicState | None = None
    entrenchment: EpistemicEntrenchment | None = None


@dataclass(frozen=True)
class FormalDecision:
    projection: FormalProjectionBundle
    outcome: BeliefSet | RevisionOutcome | ICMergeOutcome | SpohnEpistemicState
    operation: str


def is_formal_budget_error(exc: BaseException) -> bool:
    return isinstance(exc, AlphabetBudgetExceeded | EnumerationExceeded)


__all__ = [
    "FormalDecision",
    "FormalProjectionBundle",
    "expand",
    "full_meet_contract",
    "is_formal_budget_error",
    "lexicographic_revise",
    "merge_belief_profile",
    "restrained_revise",
    "revise",
]
