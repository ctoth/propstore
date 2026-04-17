from __future__ import annotations

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import RevisionAtomExplanation, RevisionExplanation
from propstore.support_revision.state import RevisionResult


def build_revision_explanation(
    result: RevisionResult,
    *,
    entrenchment: EntrenchmentReport | None = None,
) -> RevisionExplanation:
    """Build a stable default explanation payload for a revision result."""
    accepted_ids = tuple(result.accepted_atom_ids)
    rejected_ids = tuple(result.rejected_atom_ids)
    atom_ids = sorted({
        *accepted_ids,
        *rejected_ids,
        *result.explanation.keys(),
    })
    accepted_set = set(accepted_ids)

    atoms: dict[str, RevisionAtomExplanation] = {}
    for atom_id in atom_ids:
        detail = result.explanation.get(atom_id)
        status = "accepted" if atom_id in accepted_set else "rejected"
        reason = (
            detail.reason
            if detail is not None and detail.reason is not None
            else ("unchanged" if status == "accepted" else "rejected")
        )

        atoms[atom_id] = RevisionAtomExplanation(
            status=status,
            reason=reason,
            ranking=(
                None
                if entrenchment is None
                else entrenchment.reasons.get(atom_id)
            ),
            incision_set=() if detail is None else detail.incision_set,
            support_sets=() if detail is None else detail.support_sets,
        )

    return RevisionExplanation(
        accepted_atom_ids=accepted_ids,
        rejected_atom_ids=rejected_ids,
        incision_set=tuple(result.incision_set),
        atoms=atoms,
    )
