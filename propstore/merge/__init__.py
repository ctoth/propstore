"""Semantic repository merge services.

The merge boundary emits a formal partial argumentation framework over the claim
alternatives that survive a three-way merge (``merge_classifier``), summarizes its
acceptance state (``merge_report``), and projects each branch into a structured Dung
framework merged with the argumentation package's AF-merge operators
(``structured_merge``). Rival normalizations are held, never collapsed (CLAUDE.md).

The two-parent storage commit (``create_merge_commit``) and the family-materialized
``MergeManifest`` are deferred to Phase 9: they need the ``Repository`` / snapshot
facade that binds git and the family registry, which does not exist yet.
"""

from propstore.merge.merge_claims import MergeClaim
from propstore.merge.merge_classifier import (
    IntegrityConstraint,
    IntegrityConstraintViolation,
    MergeArgument,
    MergeComparisonProvenanceError,
    RepositoryMergeFramework,
    build_merge_framework,
)
from propstore.merge.merge_report import (
    semantic_candidate_details,
    summarize_merge_framework,
)
from propstore.merge.structured_merge import (
    BranchArgumentationEvidence,
    BranchStructuredSummary,
    MergeStanceRow,
    argumentation_evidence_from_projection,
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from propstore.merge.witness import ProvenanceWitness

__all__ = [
    "BranchArgumentationEvidence",
    "BranchStructuredSummary",
    "IntegrityConstraint",
    "IntegrityConstraintViolation",
    "MergeArgument",
    "MergeClaim",
    "MergeComparisonProvenanceError",
    "MergeStanceRow",
    "ProvenanceWitness",
    "RepositoryMergeFramework",
    "argumentation_evidence_from_projection",
    "build_branch_structured_summary",
    "build_merge_framework",
    "build_structured_merge_candidates",
    "semantic_candidate_details",
    "summarize_merge_framework",
]
