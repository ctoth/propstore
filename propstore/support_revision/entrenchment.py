from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from propstore.support_revision.belief_set_adapter import (
    EpistemicEntrenchment,
    Formula,
    project_formal_bundle,
)
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.state import (
    BeliefBase,
)


@dataclass(frozen=True)
class EntrenchmentReport:
    ranked_atom_ids: tuple[str, ...]
    reasons: Mapping[str, EntrenchmentReason] = field(
        default_factory=dict[str, EntrenchmentReason]
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ranked_atom_ids",
            tuple(str(atom_id) for atom_id in self.ranked_atom_ids),
        )
        object.__setattr__(
            self,
            "reasons",
            {str(atom_id): reason for atom_id, reason in self.reasons.items()},
        )


def compute_entrenchment(base: BeliefBase) -> EntrenchmentReport:
    """Compute formal ordering plus support-level explanation reasons.

    The ordering is derived from ``base`` and its formal entrenchment projection.
    """
    bundle = project_formal_bundle(base)
    formal = bundle.entrenchment
    if formal is None:
        raise ValueError("formal entrenchment projection is unavailable")

    reasons: dict[str, EntrenchmentReason] = {}
    atom_ids = tuple(sorted(atom.atom_id for atom in base.atoms))

    for atom in base.atoms:
        support_count = len(atom.label.environments) if atom.label is not None else 0

        reasons[atom.atom_id] = EntrenchmentReason(
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
        1 for other_atom_id in atom_ids if formal.leq(formulas[other_atom_id], formula)
    )


def _entrenchment_sort_key(
    atom_id: str,
    formal: EpistemicEntrenchment,
    formulas: Mapping[str, Formula],
    atom_ids: tuple[str, ...],
    reasons: Mapping[str, EntrenchmentReason],
) -> tuple[int, int, str]:
    reason = reasons[atom_id]
    return (
        -(reason.support_count or 0),
        -_formal_rank_position(formal, formulas, atom_id, atom_ids),
        atom_id,
    )
