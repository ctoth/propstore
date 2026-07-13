from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.support_revision.belief_set_adapter import (
    EpistemicEntrenchment,
    Formula,
    project_formal_bundle,
)
from propstore.support_revision.explanation_types import (
    EntrenchmentReason,
    coerce_override_priority,
)
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    is_assertion_atom,
    is_assumption_atom,
)


@dataclass(frozen=True)
class EntrenchmentReport:
    ranked_atom_ids: tuple[str, ...]
    reasons: Mapping[str, EntrenchmentReason] = field(default_factory=dict[str, EntrenchmentReason])

    def __post_init__(self) -> None:
        object.__setattr__(self, "ranked_atom_ids", tuple(str(atom_id) for atom_id in self.ranked_atom_ids))
        object.__setattr__(
            self,
            "reasons",
            {str(atom_id): reason for atom_id, reason in self.reasons.items()},
        )


def compute_entrenchment(
    bound: object,
    base: BeliefBase,
    *,
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> EntrenchmentReport:
    """Compute formal ordering plus support-level explanation reasons.

    ``bound`` is accepted to keep the world-bound call signature stable; the
    ordering itself is derived from ``base`` and the formal entrenchment
    projection, so the bound world is not read here.
    """
    override_items: list[tuple[str, Mapping[str, Any]]] = (
        [] if overrides is None else list(overrides.items())
    )
    override_map = {str(k): dict(v) for k, v in override_items}
    bundle = project_formal_bundle(base)
    formal = bundle.entrenchment
    if formal is None:
        raise ValueError("formal entrenchment projection is unavailable")

    reasons: dict[str, EntrenchmentReason] = {}
    atom_ids = tuple(sorted(atom.atom_id for atom in base.atoms))

    for atom in base.atoms:
        _, override_key, override = _match_override(atom, base, override_map)

        support_count = (
            len(atom.label.environments)
            if atom.label is not None
            else 0
        )

        reasons[atom.atom_id] = EntrenchmentReason(
            override_priority=(
                None
                if override is None
                else coerce_override_priority(override.get("priority"))
            ),
            override_key=override_key,
            support_count=support_count,
            essential_support=tuple(base.essential_support.get(atom.atom_id, ())),
        )

    ranked_atom_ids = tuple(
        sorted(
            atom_ids,
            key=lambda atom_id: _entrenchment_sort_key(
                atom_id,
                formal,
                bundle.formula_by_atom_id,
                atom_ids,
                reasons,
            ),
        )
    )
    return EntrenchmentReport(
        ranked_atom_ids=ranked_atom_ids,
        reasons=reasons,
    )


def _formal_rank_position(
    formal: EpistemicEntrenchment,
    formulas: Mapping[str, Formula],
    atom_id: str,
    atom_ids: tuple[str, ...],
) -> int:
    formula = formulas[atom_id]
    return sum(
        1
        for other_atom_id in atom_ids
        if formal.leq(formulas[other_atom_id], formula)
    )


def _entrenchment_sort_key(
    atom_id: str,
    formal: EpistemicEntrenchment,
    formulas: Mapping[str, Formula],
    atom_ids: tuple[str, ...],
    reasons: Mapping[str, EntrenchmentReason],
) -> tuple[int, tuple[int, int | str], int, int, str]:
    reason = reasons[atom_id]
    return (
        0 if reason.override_priority is not None else 1,
        _override_priority_sort_key(reason.override_priority),
        -(reason.support_count or 0),
        -_formal_rank_position(formal, formulas, atom_id, atom_ids),
        atom_id,
    )


def _override_priority_sort_key(priority: int | str | None) -> tuple[int, int | str]:
    if priority is None:
        return (2, "")
    if isinstance(priority, int):
        return (0, priority)
    return (1, priority)


def _match_override(
    atom: BeliefAtom,
    base: BeliefBase,
    override_map: Mapping[str, Mapping[str, Any]],
) -> tuple[int, str | None, Mapping[str, Any] | None]:
    candidates: list[tuple[int, str]] = [(0, atom.atom_id)]

    for source_id in _override_source_ids(atom):
        candidates.append((1, f"source:{source_id}"))

    context_id = base.scope.context_id
    if context_id:
        candidates.append((1, f"context:{context_id}"))

    candidates.append((2, "kind:assumption" if is_assumption_atom(atom) else "kind:assertion"))

    for rank, key in candidates:
        override = override_map.get(key)
        if override is not None:
            return rank, key, override
    return 3, None, None


def _override_source_ids(atom: BeliefAtom) -> tuple[str, ...]:
    if not is_assertion_atom(atom):
        return ()

    values: list[str] = []
    for claim in atom.source_claims:
        source_paper = claim.attribute_value("source_paper")
        if source_paper:
            values.append(str(source_paper))
    return tuple(dict.fromkeys(values))
