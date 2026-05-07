from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from propstore.core.id_types import AssumptionId
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import RevisionAtomDetail
from propstore.support_revision.belief_set_adapter import (
    FormalDecision,
    accepted_atom_ids as formal_accepted_atom_ids,
    decide_contract,
    decide_expand,
    decide_revise,
    rejected_atom_ids as formal_rejected_atom_ids,
)
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    AssumptionAtom,
    AssertionAtom,
    RevisionResult,
    SupportRevisionRealization,
    is_assumption_atom,
    is_assertion_atom,
)


FORMAL_MAX_ALPHABET_SIZE = 16


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
    if kind == "assertion":
        assertion_id = revision_input.get("assertion_id") or revision_input.get("id") or revision_input.get("atom_id")
        if not assertion_id:
            raise ValueError("Assertion revision input requires 'assertion_id' or 'id'")
        existing = _find_existing_atom(base, str(assertion_id))
        if existing is not None:
            return existing
        raise ValueError(f"Unknown revision input: {assertion_id}")

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
    decision = decide_expand(
        base,
        atom,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(base, decision, extra_atoms=(atom,), accepted_reason="expanded")


def contract(
    base: BeliefBase,
    targets: str | BeliefAtom | Mapping[str, Any] | Sequence[str | BeliefAtom | Mapping[str, Any]],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
) -> RevisionResult:
    """Contract a belief base by realizing the formal belief-set contraction."""
    target_ids = _normalize_targets(base, targets)
    decision = decide_contract(
        base,
        target_ids,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(base, decision, rejected_reason="contracted")


def revise(
    base: BeliefBase,
    atom: BeliefAtom | str | Mapping[str, Any],
    *,
    entrenchment: EntrenchmentReport,
    max_candidates: int,
    conflicts: Mapping[str, Sequence[str]] | None = None,
) -> RevisionResult:
    """Revise by realizing the formal belief-set revision decision."""
    atom = normalize_revision_input(base, atom)
    conflict_ids = _conflicts_for_atom(atom.atom_id, conflicts)
    decision = decide_revise(
        base,
        atom,
        conflicts=conflict_ids,
        max_alphabet_size=FORMAL_MAX_ALPHABET_SIZE,
    )
    return realize_formal_decision(
        base,
        decision,
        extra_atoms=(atom,),
        accepted_reason="revised_in",
        rejected_reason="revised_out",
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


def realize_formal_decision(
    base: BeliefBase,
    decision: FormalDecision,
    *,
    extra_atoms: tuple[BeliefAtom, ...] = (),
    accepted_reason: str = "formally_accepted",
    rejected_reason: str = "formally_rejected",
) -> RevisionResult:
    atoms_by_id = {atom.atom_id: atom for atom in base.atoms}
    for atom in extra_atoms:
        atoms_by_id.setdefault(atom.atom_id, atom)

    accepted_ids = tuple(
        atom_id
        for atom_id in formal_accepted_atom_ids(decision)
        if atom_id in atoms_by_id
    )
    rejected_ids = tuple(
        atom_id
        for atom_id in formal_rejected_atom_ids(decision)
        if atom_id in atoms_by_id
    )
    incision_set = _support_realization_cuts(base, rejected_ids)
    explanation: dict[str, RevisionAtomDetail] = {}
    for atom_id in accepted_ids:
        if atom_id in {atom.atom_id for atom in extra_atoms}:
            explanation[atom_id] = RevisionAtomDetail(reason=accepted_reason)
    for atom_id in rejected_ids:
        explanation[atom_id] = RevisionAtomDetail(
            reason=rejected_reason,
            incision_set=incision_set,
            support_sets=tuple(base.support_sets.get(atom_id, ())),
        )

    revised_base = _rebuild_base(
        base,
        tuple(atoms_by_id[atom_id] for atom_id in accepted_ids),
    )
    realization = SupportRevisionRealization(
        accepted_atom_ids=accepted_ids,
        rejected_atom_ids=rejected_ids,
        incision_set=incision_set,
        source_claim_ids=_source_claim_ids(atoms_by_id, accepted_ids),
        reasons=explanation,
    )
    return RevisionResult(
        revised_base=revised_base,
        accepted_atom_ids=accepted_ids,
        rejected_atom_ids=rejected_ids,
        incision_set=incision_set,
        explanation=explanation,
        decision=decision.report,
        realization=realization,
    )


def _conflicts_for_atom(
    atom_id: str,
    conflicts: Mapping[str, Sequence[str]] | None,
) -> tuple[str, ...]:
    if conflicts is None:
        return ()
    return tuple(str(conflict) for conflict in conflicts.get(atom_id, ()))


def _support_realization_cuts(
    base: BeliefBase,
    rejected_atom_ids: Sequence[str],
) -> tuple[str, ...]:
    rejected = set(rejected_atom_ids)
    cuts = {
        str(assumption_id)
        for atom_id in rejected
        for support_set in base.support_sets.get(atom_id, ())
        for assumption_id in support_set
    }
    return tuple(sorted(cuts))


def _source_claim_ids(
    atoms_by_id: Mapping[str, BeliefAtom],
    accepted_atom_ids: Sequence[str],
) -> tuple[str, ...]:
    claim_ids: list[str] = []
    for atom_id in accepted_atom_ids:
        atom = atoms_by_id.get(atom_id)
        if atom is None or not is_assertion_atom(atom):
            continue
        claim_ids.extend(str(claim.claim_id) for claim in atom.source_claims)
    return tuple(dict.fromkeys(claim_ids))


def _has_surviving_support(
    support_sets: Sequence[Sequence[AssumptionId]],
    incision_set: Sequence[str],
) -> bool:
    incised = set(incision_set)
    return any(all(assumption_id not in incised for assumption_id in support_set) for support_set in support_sets)


def _rebuild_base(base: BeliefBase, atoms: Sequence[BeliefAtom]) -> BeliefBase:
    accepted_ids = {atom.atom_id for atom in atoms}
    supporting_assumption_ids = {
        str(assumption_id)
        for atom_id, support_sets in base.support_sets.items()
        if atom_id in accepted_ids
        for support_set in support_sets
        for assumption_id in support_set
    }
    assumptions = tuple(
        assumption
        for assumption in base.assumptions
        if f"assumption:{assumption.assumption_id}" in accepted_ids
        or assumption.assumption_id in accepted_ids
        or assumption.assumption_id in supporting_assumption_ids
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
