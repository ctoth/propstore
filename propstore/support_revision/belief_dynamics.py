from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from propstore.support_revision.belief_set_adapter import (
    decide_contract,
    decide_expand,
    decide_revise,
)
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.input_normalization import normalize_revision_input
from propstore.support_revision.realization import realize_formal_decision
from propstore.support_revision.state import (
    AssumptionAtom,
    AssertionAtom,
    BeliefAtom,
    BeliefBase,
    RevisionResult,
)


FORMAL_MAX_ALPHABET_SIZE = 16


def expand_belief_base(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
) -> RevisionResult:
    """Project to the formal kernel, expand, then realize support consequences."""
    normalized = normalize_revision_input(base, atom)
    decision = decide_expand(
        base,
        normalized,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(base, decision, extra_atoms=(normalized,), accepted_reason="expanded")


def contract_belief_base(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
) -> RevisionResult:
    """Project to the formal kernel, contract, then realize support consequences."""
    target_ids = _normalize_targets(base, targets)
    decision = decide_contract(
        base,
        target_ids,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(
        base,
        decision,
        rejected_reason="contracted",
        support_entrenchment=entrenchment,
        max_candidates=max_candidates,
    )


def revise_belief_base(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
    conflicts: Mapping[str, Sequence[str]] | None = None,
) -> RevisionResult:
    """Project to the formal kernel, revise, then realize support consequences."""
    normalized = normalize_revision_input(base, atom)
    conflict_ids = _conflicts_for_atom(normalized.atom_id, conflicts)
    decision = decide_revise(
        base,
        normalized,
        conflicts=conflict_ids,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(
        base,
        decision,
        extra_atoms=(normalized,),
        accepted_reason="revised_in",
        rejected_reason="revised_out",
        support_entrenchment=entrenchment,
        max_candidates=max_candidates,
    )


def _normalize_targets(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
) -> tuple[str, ...]:
    if isinstance(targets, (str, Mapping)):
        return (normalize_revision_input(base, targets).atom_id,)
    if isinstance(targets, tuple) and len(targets) == 0:
        return ()
    if isinstance(targets, list) and len(targets) == 0:
        return ()
    if isinstance(targets, Sequence) and not isinstance(targets, (AssertionAtom, AssumptionAtom)):
        return tuple(normalize_revision_input(base, target).atom_id for target in targets)
    return (normalize_revision_input(base, targets).atom_id,)


def _conflicts_for_atom(
    atom_id: str,
    conflicts: Mapping[str, Sequence[str]] | None,
) -> tuple[str, ...]:
    if conflicts is None:
        return ()
    return tuple(str(conflict) for conflict in conflicts.get(atom_id, ()))
