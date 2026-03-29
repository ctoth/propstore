from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from itertools import combinations
from typing import Any

from propstore.revision.entrenchment import EntrenchmentReport
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionResult


def normalize_revision_input(
    base: BeliefBase,
    revision_input: BeliefAtom | str | Mapping[str, Any],
) -> BeliefAtom:
    """Normalize a user-facing revision input into a BeliefAtom."""
    if isinstance(revision_input, BeliefAtom):
        return revision_input

    if isinstance(revision_input, str):
        existing = _find_existing_atom(base, revision_input)
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {revision_input}")

    kind = str(revision_input.get("kind") or "claim")
    if kind == "claim":
        claim_id = revision_input.get("id") or revision_input.get("claim_id")
        if not claim_id:
            raise ValueError("Claim revision input requires 'id' or 'claim_id'")
        atom_id = str(revision_input.get("atom_id") or f"claim:{claim_id}")
        return BeliefAtom(atom_id=atom_id, kind="claim", payload=dict(revision_input))

    if kind == "assumption":
        assumption_id = revision_input.get("assumption_id") or revision_input.get("id")
        if not assumption_id:
            raise ValueError("Assumption revision input requires 'assumption_id' or 'id'")
        atom_id = str(revision_input.get("atom_id") or f"assumption:{assumption_id}")
        return BeliefAtom(atom_id=atom_id, kind="assumption", payload=dict(revision_input))

    raise ValueError(f"Unsupported revision input kind: {kind}")


def expand(base: BeliefBase, atom: BeliefAtom | str | Mapping[str, Any]) -> RevisionResult:
    """Expand a finite belief base by one atom without mutating the input base."""
    atom = normalize_revision_input(base, atom)
    atom_by_id = {existing.atom_id: existing for existing in base.atoms}
    atom_by_id.setdefault(atom.atom_id, atom)
    revised_base = _rebuild_base(base, atom_by_id.values())
    accepted = tuple(item.atom_id for item in revised_base.atoms)
    explanation = {atom.atom_id: {"reason": "expanded"}} if atom.atom_id in accepted else {}
    return RevisionResult(
        revised_base=revised_base,
        accepted_atom_ids=accepted,
        rejected_atom_ids=(),
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

    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    explanation: dict[str, dict[str, object]] = {}

    for atom in base.atoms:
        atom_id = atom.atom_id
        if atom_id in incision_set:
            rejected_ids.append(atom_id)
            explanation[atom_id] = {
                "reason": "incised",
                "incision_set": incision_set,
            }
            continue

        if atom.kind == "claim":
            support_sets = base.support_sets.get(atom_id, ())
            if support_sets and not _has_surviving_support(support_sets, incision_set):
                rejected_ids.append(atom_id)
                explanation[atom_id] = {
                    "reason": "support_lost",
                    "incision_set": incision_set,
                    "support_sets": support_sets,
                }
                continue
            if atom_id in target_ids and not support_sets:
                rejected_ids.append(atom_id)
                explanation[atom_id] = {
                    "reason": "contracted",
                    "incision_set": incision_set,
                }
                continue

        accepted_ids.append(atom_id)

    accepted_set = set(accepted_ids)
    revised_base = _rebuild_base(
        base,
        [atom for atom in base.atoms if atom.atom_id in accepted_set],
    )
    return RevisionResult(
        revised_base=revised_base,
        accepted_atom_ids=tuple(accepted_ids),
        rejected_atom_ids=tuple(rejected_ids),
        incision_set=incision_set,
        explanation=explanation,
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


def _normalize_targets(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
) -> tuple[str, ...]:
    if isinstance(targets, (str, BeliefAtom, Mapping)):
        return (normalize_revision_input(base, targets).atom_id,)
    return tuple(normalize_revision_input(base, target).atom_id for target in targets)


def _find_existing_atom(base: BeliefBase, revision_input: str) -> BeliefAtom | None:
    for atom in base.atoms:
        if atom.atom_id == revision_input:
            return atom
        if atom.kind == "claim" and atom.payload.get("id") == revision_input:
            return atom
        if atom.kind == "assumption" and atom.payload.get("assumption_id") == revision_input:
            return atom
    return None


def _choose_incision_set(
    base: BeliefBase,
    target_ids: Sequence[str],
    entrenchment: EntrenchmentReport,
) -> tuple[str, ...]:
    support_sets = [
        tuple(support_set)
        for target_id in target_ids
        for support_set in base.support_sets.get(target_id, ())
    ]
    if not support_sets:
        return tuple(sorted(target_ids))

    candidates = sorted({assumption_id for support_set in support_sets for assumption_id in support_set})
    rank_index = {atom_id: idx for idx, atom_id in enumerate(entrenchment.ranked_atom_ids)}
    fallback_rank = len(entrenchment.ranked_atom_ids) + len(candidates)

    best_combo: tuple[str, ...] | None = None
    best_score: tuple[int, int, tuple[str, ...]] | None = None
    for size in range(1, len(candidates) + 1):
        for combo in combinations(candidates, size):
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


def _has_surviving_support(
    support_sets: Sequence[Sequence[str]],
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
