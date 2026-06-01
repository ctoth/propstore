from __future__ import annotations

from dataclasses import dataclass

from propstore.support_revision.state import EpistemicState, RevisionResult


@dataclass(frozen=True)
class _CaptureBound:
    state: EpistemicState
    result: RevisionResult

    def epistemic_state(self) -> EpistemicState:
        return self.state

    def revise(self, atom, *, conflicts, max_candidates):
        return self.result

    def revision_explain(self, result):
        return {"accepted_atom_ids": list(result.accepted_atom_ids)}
