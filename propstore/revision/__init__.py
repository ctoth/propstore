"""Revision-facing projection and entrenchment helpers."""

from propstore.revision.entrenchment import EntrenchmentReport, compute_entrenchment
from propstore.revision.operators import contract, expand, normalize_revision_input, revise
from propstore.revision.projection import project_belief_base
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionResult, RevisionScope

__all__ = [
    "BeliefAtom",
    "BeliefBase",
    "EntrenchmentReport",
    "RevisionResult",
    "RevisionScope",
    "contract",
    "compute_entrenchment",
    "expand",
    "normalize_revision_input",
    "project_belief_base",
    "revise",
]
