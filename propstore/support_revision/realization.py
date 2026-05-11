from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from itertools import combinations

from propstore.core.anytime import EnumerationExceeded
from propstore.core.id_types import AssumptionId
from propstore.support_revision.belief_set_adapter import (
    FormalDecision,
    accepted_atom_ids as formal_accepted_atom_ids,
    rejected_atom_ids as formal_rejected_atom_ids,
    selected_world_atom_ids,
)
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import RevisionAtomDetail
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    RevisionMergeRequiredFailure,
    RevisionResult,
    SupportRevisionRealization,
    is_assertion_atom,
)


def realize_formal_decision(
    base: BeliefBase,
    decision: FormalDecision,
    *,
    extra_atoms: tuple[BeliefAtom, ...] = (),
    accepted_reason: str = "formally_accepted",
    rejected_reason: str = "formally_rejected",
    support_entrenchment: EntrenchmentReport | None = None,
    max_candidates: int | None = None,
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
    working_base = _rebuild_base(
        base,
        tuple(atoms_by_id[atom_id] for atom_id in atoms_by_id),
    )
    incision_set = _support_realization_cuts(
        working_base,
        rejected_ids,
        support_entrenchment=support_entrenchment,
        max_candidates=max_candidates,
    )
    forced_rejections = _forced_support_rejections(working_base, rejected_ids, incision_set)
    stabilized = stabilize_belief_base(
        working_base,
        incision_set=incision_set,
        forced_rejections=forced_rejections,
    )
    explanation: dict[str, RevisionAtomDetail] = dict(stabilized.explanation)
    for atom_id in accepted_ids:
        if atom_id in stabilized.accepted_atom_ids and atom_id in {atom.atom_id for atom in extra_atoms}:
            explanation[atom_id] = RevisionAtomDetail(reason=accepted_reason)
    for atom_id in rejected_ids:
        explanation.setdefault(
            atom_id,
            RevisionAtomDetail(
                reason=rejected_reason,
                incision_set=incision_set,
                support_sets=tuple(working_base.support_sets.get(atom_id, ())),
            ),
        )
    realization = SupportRevisionRealization(
        accepted_atom_ids=stabilized.accepted_atom_ids,
        rejected_atom_ids=stabilized.rejected_atom_ids,
        incision_set=incision_set,
        source_claim_ids=_source_claim_ids(atoms_by_id, stabilized.accepted_atom_ids),
        reasons=explanation,
    )
    return RevisionResult(
        revised_base=stabilized.revised_base,
        accepted_atom_ids=stabilized.accepted_atom_ids,
        rejected_atom_ids=stabilized.rejected_atom_ids,
        incision_set=incision_set,
        explanation=explanation,
        decision=decision.report,
        realization=realization,
    )


def realize_ic_merge_decision(
    base: BeliefBase,
    decision: FormalDecision,
) -> RevisionResult:
    selected_worlds = selected_world_atom_ids(decision)
    if not selected_worlds:
        raise _ic_merge_failure("unsatisfiable_integrity_constraint", decision)
    if len(selected_worlds) != 1:
        raise _ic_merge_failure("ambiguous_selected_worlds", decision)

    atoms_by_id = {atom.atom_id: atom for atom in base.atoms}
    projected_atom_ids = tuple(atom_id for atom_id in decision.projection.formula_by_atom_id if atom_id in atoms_by_id)
    selected = set(selected_worlds[0])
    accepted_ids = tuple(atom_id for atom_id in projected_atom_ids if atom_id in selected)
    rejected_ids = tuple(atom_id for atom_id in projected_atom_ids if atom_id not in selected)
    missing = tuple(atom_id for atom_id in selected if atom_id not in atoms_by_id)
    if missing:
        raise _ic_merge_failure("unmapped_formal_atom", decision)

    revised_base = _rebuild_base(
        base,
        tuple(atoms_by_id[atom_id] for atom_id in accepted_ids),
    )
    explanation = {
        atom_id: RevisionAtomDetail(
            reason="ic_merge_world_true",
            selection_rule="ic_merge_selected_world",
            support_sets=tuple(base.support_sets.get(atom_id, ())),
        )
        for atom_id in accepted_ids
    }
    explanation.update(
        {
            atom_id: RevisionAtomDetail(
                reason="ic_merge_world_false",
                selection_rule="ic_merge_selected_world",
                support_sets=tuple(base.support_sets.get(atom_id, ())),
            )
            for atom_id in rejected_ids
        }
    )
    realization = SupportRevisionRealization(
        accepted_atom_ids=accepted_ids,
        rejected_atom_ids=rejected_ids,
        incision_set=(),
        source_claim_ids=_source_claim_ids(atoms_by_id, accepted_ids),
        reasons=explanation,
        journal_metadata={
            "selected_world": list(selected_worlds[0]),
            "selected_worlds_hash": decision.report.trace.get("selected_worlds_hash"),
        },
    )
    return RevisionResult(
        revised_base=revised_base,
        accepted_atom_ids=accepted_ids,
        rejected_atom_ids=rejected_ids,
        incision_set=(),
        explanation=explanation,
        decision=decision.report,
        realization=realization,
    )


def _ic_merge_failure(reason: str, decision: FormalDecision) -> RevisionMergeRequiredFailure:
    trace = decision.report.trace
    return RevisionMergeRequiredFailure(
        reason=reason,
        decision_report=decision.report,
        profile_atom_ids=_trace_profile_atom_ids(trace.get("profile_atom_ids") or ()),
        integrity_constraint=_trace_integrity_constraint(trace.get("integrity_constraint")),
        selected_worlds_hash=trace.get("selected_worlds_hash"),
    )


def _trace_profile_atom_ids(value: object) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    profiles: list[tuple[str, ...]] = []
    for profile in value:
        if not isinstance(profile, Sequence) or isinstance(profile, str):
            return ()
        profiles.append(tuple(str(atom_id) for atom_id in profile))
    return tuple(profiles)


def _trace_integrity_constraint(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return dict(value)


def stabilize_belief_base(
    base: BeliefBase,
    *,
    incision_set: Sequence[str] = (),
    forced_rejections: Sequence[str] = (),
) -> RevisionResult:
    """Recompute support acceptance until stable under the given incision set."""
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
                        selection_rule="minimal_support_incision",
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


def _support_realization_cuts(
    base: BeliefBase,
    rejected_atom_ids: Sequence[str],
    *,
    support_entrenchment: EntrenchmentReport | None,
    max_candidates: int | None,
) -> tuple[str, ...]:
    rejected = set(rejected_atom_ids)
    support_sets = [
        tuple(str(assumption_id) for assumption_id in support_set)
        for atom_id in rejected
        for support_set in base.support_sets.get(atom_id, ())
    ]
    if not support_sets:
        return tuple(sorted(atom_id for atom_id in rejected if atom_id.startswith("assumption:")))

    candidates = sorted({assumption_id for support_set in support_sets for assumption_id in support_set})
    rank_index = (
        {}
        if support_entrenchment is None
        else {atom_id: idx for idx, atom_id in enumerate(support_entrenchment.ranked_atom_ids)}
    )
    fallback_rank = len(rank_index) + len(candidates)
    best_combo: tuple[str, ...] | None = None
    best_score: tuple[int, int, tuple[str, ...]] | None = None
    examined = 0
    for size in range(1, len(candidates) + 1):
        for combo in combinations(candidates, size):
            if max_candidates is not None and examined >= max_candidates:
                raise EnumerationExceeded(
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


def _forced_support_rejections(
    base: BeliefBase,
    rejected_atom_ids: Sequence[str],
    incision_set: Sequence[str],
) -> tuple[str, ...]:
    incised = set(incision_set)
    forced: list[str] = []
    for atom_id in rejected_atom_ids:
        if atom_id in incised:
            continue
        if base.support_sets.get(atom_id):
            continue
        forced.append(atom_id)
    return tuple(forced)


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
