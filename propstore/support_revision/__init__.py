"""Support-incision helpers for scoped worldline capture.

This package is not AGM belief revision. Formal AGM, iterated revision, and IC
merge live in the external ``belief_set`` package. Formal AF revision lives in
``argumentation.af_revision``.
"""

from propstore.support_revision.af_adapter import (
    RevisionArgumentationStore,
    RevisionArgumentationView,
    project_epistemic_state_argumentation_view,
)
from propstore.support_revision.entrenchment import EntrenchmentReport, compute_entrenchment
from propstore.support_revision.explain import build_revision_explanation
from propstore.support_revision.iterated import advance_epistemic_state, epistemic_state_payload, iterated_revise, make_epistemic_state
from propstore.support_revision.operators import contract, expand, normalize_revision_input, stabilize_belief_base
from propstore.support_revision.projection import project_belief_base
from propstore.support_revision.state import BeliefAtom, BeliefBase, EpistemicState, RevisionEpisode, RevisionResult, RevisionScope

__all__ = [
    "BeliefAtom",
    "BeliefBase",
    "EpistemicState",
    "EntrenchmentReport",
    "RevisionArgumentationStore",
    "RevisionArgumentationView",
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
    "project_epistemic_state_argumentation_view",
    "project_belief_base",
    "stabilize_belief_base",
]
