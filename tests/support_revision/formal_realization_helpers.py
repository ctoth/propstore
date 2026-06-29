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
from propstore.support_revision.input_normalization import normalize_revision_input
from propstore.support_revision.realization import realize_formal_decision
from propstore.support_revision.state import (
    AssumptionAtom,
    AssertionAtom,
    BeliefAtom,
    BeliefBase,
    RevisionResult,
)


def expand_via_formal_decision(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
) -> RevisionResult:
    normalized = normalize_revision_input(base, atom)
    decision = decide_expand(
        base,
        normalized,
        max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(
        base,
        decision,
        extra_atoms=(normalized,),
        accepted_reason="expanded",
    )


def contract_via_formal_decision(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
) -> RevisionResult:
    decision = decide_contract(
        base,
        _normalize_targets(base, targets),
        max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(
        base,
        decision,
        rejected_reason="contracted",
        support_entrenchment=entrenchment,
        max_candidates=max_candidates,
    )


def revise_via_formal_decision(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
    conflicts: Mapping[str, Sequence[str]] | None = None,
) -> RevisionResult:
    normalized = normalize_revision_input(base, atom)
    decision = decide_revise(
        base,
        normalized,
        conflicts=_conflicts_for_atom(normalized.atom_id, conflicts),
        max_alphabet_size=DEFAULT_MAX_ALPHABET_SIZE,
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
