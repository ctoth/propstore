"""Support-incision helpers for scoped worldline capture.

This package is not AGM belief revision. Formal AGM, iterated revision, and IC
merge live in the external ``belief_set`` package. Formal AF revision lives in
``argumentation.dynamics.af_revision``. The single ``belief_set`` contact point
is :mod:`propstore.support_revision.belief_set_adapter`; every other module in
this package composes propstore-scoped types.
"""

from propstore.support_revision.af_adapter import (
    RevisionArgumentationStore,
    RevisionArgumentationView,
    project_epistemic_state_argumentation_view,
)
from propstore.support_revision.entrenchment import (
    EntrenchmentReport,
    compute_entrenchment,
)
from propstore.support_revision.explain import build_revision_explanation
from propstore.support_revision.input_normalization import (
    normalize_revision_input,
    parse_revision_atom_payload,
)
from propstore.support_revision.projection import project_belief_base
from propstore.support_revision.iterated import (
    advance_epistemic_state,
    epistemic_state_payload,
    iterated_revise,
    make_epistemic_state,
)
from propstore.support_revision.realization import stabilize_belief_base
from propstore.support_revision.state import (
    BeliefAtom,
    BeliefBase,
    EpistemicState,
    RevisionEpisode,
    RevisionEvent,
    RevisionMergeRequiredFailure,
    RevisionRealizationFailure,
    RevisionResult,
    RevisionScope,
)

__all__ = [
    "BeliefAtom",
    "BeliefBase",
    "EntrenchmentReport",
    "EpistemicState",
    "RevisionArgumentationStore",
    "RevisionArgumentationView",
    "RevisionEpisode",
    "RevisionEvent",
    "RevisionMergeRequiredFailure",
    "RevisionRealizationFailure",
    "RevisionResult",
    "RevisionScope",
    "advance_epistemic_state",
    "build_revision_explanation",
    "compute_entrenchment",
    "epistemic_state_payload",
    "iterated_revise",
    "make_epistemic_state",
    "normalize_revision_input",
    "parse_revision_atom_payload",
    "project_belief_base",
    "project_epistemic_state_argumentation_view",
    "stabilize_belief_base",
]
