"""Revision-facing projection and entrenchment helpers."""

from propstore.revision.entrenchment import EntrenchmentReport, compute_entrenchment
from propstore.revision.projection import project_belief_base
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope

__all__ = [
    "BeliefAtom",
    "BeliefBase",
    "EntrenchmentReport",
    "RevisionScope",
    "compute_entrenchment",
    "project_belief_base",
]
