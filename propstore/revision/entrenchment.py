from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import AssumptionId
from propstore.revision.explanation_types import (
    EntrenchmentReason,
    coerce_entrenchment_reason,
    _coerce_override_priority,
)
from propstore.revision.state import BeliefBase, is_assumption_atom, is_claim_atom


@dataclass(frozen=True)
class EntrenchmentReport:
    ranked_atom_ids: tuple[str, ...]
    reasons: Mapping[str, EntrenchmentReason] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "ranked_atom_ids", tuple(str(atom_id) for atom_id in self.ranked_atom_ids))
        object.__setattr__(
            self,
            "reasons",
            {
                str(atom_id): coerce_entrenchment_reason(reason)
                for atom_id, reason in self.reasons.items()
            },
        )


def compute_entrenchment(
    bound,
    base: BeliefBase,
    *,
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> EntrenchmentReport:
    """Compute a deterministic V1 entrenchment ordering.

    Explicit overrides outrank support-derived ordering. Support-derived ranking
    then falls back to environment coverage and stable atom id ordering.
    """
    override_map = {str(k): dict(v) for k, v in (overrides or {}).items()}
    scored: list[tuple[int, int, str]] = []
    reasons: dict[str, EntrenchmentReason] = {}

    for atom in base.atoms:
        override_rank, override_key, override = _match_override(atom, base, override_map)

        support_count = (
            len(atom.label.environments)
            if atom.label is not None
            else 0
        )

        scored.append((override_rank, -support_count, atom.atom_id))
        reasons[atom.atom_id] = EntrenchmentReason(
            override_priority=(
                None
                if override is None
                else _coerce_override_priority(override.get("priority"))
            ),
            override_key=override_key,
            support_count=support_count,
            essential_support=tuple(_essential_support_ids(bound, atom.atom_id)),
        )

    scored.sort()
    return EntrenchmentReport(
        ranked_atom_ids=tuple(atom_id for _, _, atom_id in scored),
        reasons=reasons,
    )


def _essential_support_ids(bound, atom_id: str) -> list[AssumptionId]:
    if not atom_id.startswith("claim:"):
        return []
    claim_id = atom_id.partition(":")[2]
    essential = bound.claim_essential_support(claim_id)
    if essential is None:
        return []
    return list(essential.assumption_ids)


def _match_override(
    atom,
    base: BeliefBase,
    override_map: Mapping[str, Mapping[str, Any]],
) -> tuple[int, str | None, Mapping[str, Any] | None]:
    candidates: list[tuple[int, str]] = [(0, atom.atom_id)]

    for source_id in _override_source_ids(atom):
        candidates.append((1, f"source:{source_id}"))

    context_id = base.scope.context_id
    if context_id:
        candidates.append((1, f"context:{context_id}"))

    candidates.append((2, "kind:assumption" if is_assumption_atom(atom) else "kind:claim"))

    for rank, key in candidates:
        override = override_map.get(key)
        if override is not None:
            return rank, key, override
    return 3, None, None


def _override_source_ids(atom) -> tuple[str, ...]:
    if not is_claim_atom(atom):
        return ()

    source = atom.claim.source
    provenance = atom.claim.provenance
    candidates = (
        atom.claim.source_paper,
        None if source is None else source.source_id,
        None if source is None else source.slug,
        None if provenance is None else provenance.paper,
    )
    return tuple(str(value) for value in candidates if value)
