from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.revision.entrenchment import EntrenchmentReport
from propstore.revision.state import RevisionResult


def build_revision_explanation(
    result: RevisionResult,
    *,
    entrenchment: EntrenchmentReport | None = None,
) -> dict[str, Any]:
    """Build a stable default explanation payload for a revision result."""
    accepted_ids = tuple(result.accepted_atom_ids)
    rejected_ids = tuple(result.rejected_atom_ids)
    atom_ids = sorted({
        *accepted_ids,
        *rejected_ids,
        *result.explanation.keys(),
    })
    accepted_set = set(accepted_ids)

    atoms: dict[str, dict[str, Any]] = {}
    for atom_id in atom_ids:
        detail = dict(result.explanation.get(atom_id, {}))
        status = "accepted" if atom_id in accepted_set else "rejected"
        reason = str(detail.pop("reason", "unchanged" if status == "accepted" else "rejected"))

        atom_entry: dict[str, Any] = {
            "status": status,
            "reason": reason,
        }
        atom_entry.update(_normalize_detail(detail))

        if entrenchment is not None:
            ranking = entrenchment.reasons.get(atom_id)
            if ranking is not None:
                atom_entry["ranking"] = dict(ranking)

        atoms[atom_id] = atom_entry

    return {
        "accepted_atom_ids": accepted_ids,
        "rejected_atom_ids": rejected_ids,
        "incision_set": tuple(result.incision_set),
        "atoms": atoms,
    }


def _normalize_detail(detail: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in detail.items():
        if key in {"incision_set", "support_sets"} and isinstance(value, tuple):
            normalized[key] = tuple(value)
            continue
        normalized[key] = value
    return normalized
