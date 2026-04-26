from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from itertools import combinations
from typing import Any, overload

from propstore.core.anytime import EnumerationExceeded
from propstore.core.id_types import AssumptionId
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import RevisionAtomDetail
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    AssumptionAtom,
    AssertionAtom,
    RevisionResult,
    is_assumption_atom,
    is_assertion_atom,
)


def _assertion_input_candidates(atom: BeliefAtom) -> tuple[str, ...]:
    if not is_assertion_atom(atom):
        return ()
    return (atom.atom_id, str(atom.assertion_id))


def normalize_revision_input(
    base: BeliefBase,
    revision_input: BeliefAtom | str | Mapping[str, Any],
) -> BeliefAtom:
    """Normalize a user-facing revision input into a BeliefAtom."""
    if isinstance(revision_input, (AssertionAtom, AssumptionAtom)):
        return revision_input

    if isinstance(revision_input, str):
        existing = _find_existing_atom(base, revision_input)
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {revision_input}")

    kind = str(revision_input.get("kind") or "")
    if kind == "assumption":
        assumption_id = revision_input.get("assumption_id") or revision_input.get("id")
        if not assumption_id:
            raise ValueError("Assumption revision input requires 'assumption_id' or 'id'")
        atom_id = str(revision_input.get("atom_id") or f"assumption:{assumption_id}")
        from propstore.support_revision.state import coerce_assumption_ref

        return AssumptionAtom(atom_id=atom_id, assumption=coerce_assumption_ref(revision_input))

    raise ValueError("Assertion revision input requires an AssertionAtom")


def expand(base: BeliefBase, atom: BeliefAtom | str | Mapping[str, Any]) -> RevisionResult:
    """Expand a finite belief base by one atom without mutating the input base."""
    atom = normalize_revision_input(base, atom)
    atom_by_id = {existing.atom_id: existing for existing in base.atoms}
    atom_by_id.setdefault(atom.atom_id, atom)
    stabilized = stabilize_belief_base(
        _rebuild_base(base, tuple(atom_by_id.values())),
        incision_set=(),
    )
    explanation = dict(stabilized.explanation)
    if atom.atom_id in stabilized.accepted_atom_ids:
        explanation[atom.atom_id] = RevisionAtomDetail(reason="expanded")
    return RevisionResult(
        revised_base=stabilized.revised_base,
        accepted_atom_ids=stabilized.accepted_atom_ids,
        rejected_atom_ids=stabilized.rejected_atom_ids,
        incision_set=(),
        explanation=explanation,
    )


def contract(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
    *,
    entrenchment: EntrenchmentReport,
) -> RevisionResult:
    """Contract a belief base by cutting a minimal low-entrenchment support incision set."""
    target_ids = _normalize_targets(base, targets)
    incision_set = _choose_incision_set(base, target_ids, entrenchment)
    return stabilize_belief_base(
        base,
        incision_set=incision_set,
        forced_rejections=_forced_rejections_for_targets(base, target_ids),
    )


def revise(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
    *,
    entrenchment: EntrenchmentReport,
    conflicts: Mapping[str, Sequence[str]] | None = None,
) -> RevisionResult:
    """Revise by contracting conflicting support and then expanding the new atom."""
    atom = normalize_revision_input(base, atom)
    conflict_ids = tuple(conflicts.get(atom.atom_id, ())) if conflicts is not None else ()
    if conflict_ids:
        contracted = contract(base, conflict_ids, entrenchment=entrenchment)
    else:
        contracted = RevisionResult(
            revised_base=base,
            accepted_atom_ids=tuple(item.atom_id for item in base.atoms),
            rejected_atom_ids=(),
            incision_set=(),
            explanation={},
        )

    expanded = expand(contracted.revised_base, atom)
    explanation = dict(contracted.explanation)
    explanation.update(expanded.explanation)
    return RevisionResult(
        revised_base=expanded.revised_base,
        accepted_atom_ids=expanded.accepted_atom_ids,
        rejected_atom_ids=contracted.rejected_atom_ids,
        incision_set=contracted.incision_set,
        explanation=explanation,
    )


def stabilize_belief_base(
    base: BeliefBase,
    *,
    incision_set: Sequence[str] = (),
    forced_rejections: Sequence[str] = (),
) -> RevisionResult:
    """Recompute acceptance until the belief base is stable under the given incision set."""
    active_base = base
    forced = set(forced_rejections)
    incised = tuple(incision_set)
    explanation: dict[str, RevisionAtomDetail] = {}
    all_rejected: set[str] = set()

    while True:
        accepted_ids: list[str] = []
        round_rejected: set[str] = set()

        for atom in active_base.atoms:
            atom_id = atom.atom_id
            if atom_id in incised:
                round_rejected.add(atom_id)
                explanation.setdefault(
                    atom_id,
                    RevisionAtomDetail(
                        reason="incised",
                        incision_set=incised,
                    ),
                )
                continue

            if atom_id in forced:
                round_rejected.add(atom_id)
                explanation.setdefault(
                    atom_id,
                    RevisionAtomDetail(
                        reason="contracted",
                        incision_set=incised,
                    ),
                )
                continue

            if is_assertion_atom(atom):
                support_sets = active_base.support_sets.get(atom_id, ())
                if support_sets and not _has_surviving_support(support_sets, incised):
                    round_rejected.add(atom_id)
                    explanation.setdefault(
                        atom_id,
                        RevisionAtomDetail(
                            reason="support_lost",
                            incision_set=incised,
                            support_sets=tuple(support_sets),
                        ),
                    )
                    continue

            accepted_ids.append(atom_id)

        accepted_set = set(accepted_ids)
        all_rejected.update(round_rejected)
        rebuilt = _rebuild_base(
            active_base,
            [atom for atom in active_base.atoms if atom.atom_id in accepted_set],
        )
        if tuple(atom.atom_id for atom in rebuilt.atoms) == tuple(atom.atom_id for atom in active_base.atoms):
            return RevisionResult(
                revised_base=rebuilt,
                accepted_atom_ids=tuple(accepted_ids),
                rejected_atom_ids=tuple(sorted(all_rejected)),
                incision_set=incised,
                explanation=explanation,
            )
        active_base = rebuilt


def _normalize_targets(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
) -> tuple[str, ...]:
    if isinstance(targets, (str, AssertionAtom, AssumptionAtom, Mapping)):
        return (normalize_revision_input(base, targets).atom_id,)
    return tuple(normalize_revision_input(base, target).atom_id for target in targets)


def _find_existing_atom(base: BeliefBase, revision_input: str) -> BeliefAtom | None:
    for atom in base.atoms:
        if atom.atom_id == revision_input:
            return atom
        if is_assertion_atom(atom) and revision_input in _assertion_input_candidates(atom):
            return atom
        if is_assumption_atom(atom) and atom.assumption.assumption_id == revision_input:
            return atom
    return None


@overload
def _choose_incision_set(
    base: BeliefBase,
    target_ids: Sequence[str],
    entrenchment: EntrenchmentReport,
) -> tuple[str, ...]: ...


@overload
def _choose_incision_set(
    base: BeliefBase,
    target_ids: Sequence[str],
    entrenchment: EntrenchmentReport,
    *,
    max_candidates: None,
) -> tuple[str, ...]: ...


@overload
def _choose_incision_set(
    base: BeliefBase,
    target_ids: Sequence[str],
    entrenchment: EntrenchmentReport,
    *,
    max_candidates: int,
) -> tuple[str, ...] | EnumerationExceeded: ...


def _choose_incision_set(
    base: BeliefBase,
    target_ids: Sequence[str],
    entrenchment: EntrenchmentReport,
    *,
    max_candidates: int | None = None,
) -> tuple[str, ...] | EnumerationExceeded:
    """Choose a support incision set with an anytime candidate ceiling.

    Zilberstein 1996 frames resource-bounded search as returning a partial
    result when exhaustive optimization is interrupted. This exact hitting-set
    search reports that interruption explicitly instead of silently continuing
    into exponential work.
    """

    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative")

    support_sets: list[tuple[AssumptionId, ...]] = [
        tuple(support_set)
        for target_id in target_ids
        for support_set in base.support_sets.get(target_id, ())
    ]
    if not support_sets:
        return tuple(sorted(target_ids))

    candidates = sorted({assumption_id for support_set in support_sets for assumption_id in support_set})
    rank_index = {atom_id: idx for idx, atom_id in enumerate(entrenchment.ranked_atom_ids)}
    fallback_rank = len(entrenchment.ranked_atom_ids) + len(candidates)

    best_combo: tuple[AssumptionId, ...] | None = None
    best_score: tuple[int, int, tuple[AssumptionId, ...]] | None = None
    examined = 0
    for size in range(1, len(candidates) + 1):
        for combo in combinations(candidates, size):
            if max_candidates is not None and examined >= max_candidates:
                return EnumerationExceeded(
                    partial_count=examined,
                    max_candidates=max_candidates,
                )
            examined += 1
            combo_set = set(combo)
            if not all(any(assumption_id in combo_set for assumption_id in support_set) for support_set in support_sets):
                continue
            weakness = sum(rank_index.get(atom_id, fallback_rank) for atom_id in combo)
            score = (size, -weakness, combo)
            if best_score is None or score < best_score:
                best_score = score
                best_combo = combo
        if best_combo is not None:
            break

    return tuple(best_combo or ())


def _forced_rejections_for_targets(
    base: BeliefBase,
    target_ids: Sequence[str],
) -> tuple[str, ...]:
    atom_by_id = {atom.atom_id: atom for atom in base.atoms}
    forced: list[str] = []
    for target_id in target_ids:
        atom = atom_by_id.get(target_id)
        if atom is None:
            forced.append(target_id)
            continue
        if not is_assertion_atom(atom):
            forced.append(target_id)
            continue
        if not base.support_sets.get(target_id):
            forced.append(target_id)
    return tuple(forced)


def _has_surviving_support(
    support_sets: Sequence[Sequence[AssumptionId]],
    incision_set: Sequence[str],
) -> bool:
    incised = set(incision_set)
    return any(all(assumption_id not in incised for assumption_id in support_set) for support_set in support_sets)


def _rebuild_base(base: BeliefBase, atoms: Sequence[BeliefAtom]) -> BeliefBase:
    accepted_ids = {atom.atom_id for atom in atoms}
    assumptions = tuple(
        assumption
        for assumption in base.assumptions
        if f"assumption:{assumption.assumption_id}" in accepted_ids
        or assumption.assumption_id in accepted_ids
    )
    support_sets = {
        atom_id: support_sets
        for atom_id, support_sets in base.support_sets.items()
        if atom_id in accepted_ids
    }
    essential_support = {
        atom_id: support
        for atom_id, support in base.essential_support.items()
        if atom_id in accepted_ids
    }
    return replace(
        base,
        atoms=tuple(atoms),
        assumptions=assumptions,
        support_sets=support_sets,
        essential_support=essential_support,
    )
