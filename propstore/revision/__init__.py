"""Revision-facing projection and entrenchment helpers."""

from propstore.revision.entrenchment import EntrenchmentReport, compute_entrenchment
from propstore.revision.explain import build_revision_explanation
from propstore.revision.iterated import advance_epistemic_state, epistemic_state_payload, iterated_revise, make_epistemic_state
from propstore.revision.operators import contract, expand, normalize_revision_input, revise, stabilize_belief_base
from propstore.revision.projection import project_belief_base
from propstore.revision.state import BeliefAtom, BeliefBase, EpistemicState, RevisionEpisode, RevisionResult, RevisionScope

__all__ = [
    "BeliefAtom",
    "BeliefBase",
    "EpistemicState",
    "EntrenchmentReport",
    "RevisionEpisode",
    "RevisionResult",
    "RevisionScope",
    "advance_epistemic_state",
    "build_revision_explanation",
    "contract",
    "compute_entrenchment",
    "epistemic_state_payload",
    "expand",
    "iterated_revise",
    "make_epistemic_state",
    "normalize_revision_input",
    "project_belief_base",
    "revise",
    "stabilize_belief_base",
]
