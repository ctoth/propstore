from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.revision.state import BeliefBase


@dataclass(frozen=True)
class EntrenchmentReport:
    ranked_atom_ids: tuple[str, ...]
    reasons: Mapping[str, dict[str, Any]] = field(default_factory=dict)


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
    reasons: dict[str, dict[str, Any]] = {}

    for atom in base.atoms:
        override = override_map.get(atom.atom_id)
        if override is not None:
            override_rank = 0
        else:
            override_rank = 1

        support_count = (
            len(atom.label.environments)
            if atom.label is not None
            else 0
        )

        scored.append((override_rank, -support_count, atom.atom_id))
        reasons[atom.atom_id] = {
            "override": override.get("priority") if override is not None else None,
            "support_count": support_count,
            "essential_support": _essential_support_ids(bound, atom.atom_id),
        }

    scored.sort()
    return EntrenchmentReport(
        ranked_atom_ids=tuple(atom_id for _, _, atom_id in scored),
        reasons=reasons,
    )


def _essential_support_ids(bound, atom_id: str) -> list[str]:
    if not atom_id.startswith("claim:"):
        return []
    claim_id = atom_id.partition(":")[2]
    essential = bound.claim_essential_support(claim_id)
    if essential is None:
        return []
    return list(essential.assumption_ids)
