"""Git-backed storage layer for propstore.

Re-exports the canonical git-backed storage surface plus repository merge
primitives.
"""
from propstore.storage.git_backend import GitStore
from propstore.storage.merge_classifier import (
    MergeArgument,
    RepositoryMergeFramework,
    build_merge_framework,
)
from propstore.storage.merge_commit import create_merge_commit
from propstore.storage.merge_framework import (
    PairState,
    PartialArgumentationFramework,
    enumerate_paf_completions,
    merge_framework_edit_distance,
)
from propstore.storage.paf_merge import (
    consensual_expand,
    sum_merge_frameworks,
    max_merge_frameworks,
    leximax_merge_frameworks,
)
from propstore.storage.paf_queries import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)
from propstore.storage.merge_report import summarize_merge_framework
from propstore.storage.structured_merge import (
    BranchStructuredSummary,
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from propstore.storage.repository_import import (
    RepositoryImportPlan,
    RepositoryImportResult,
    commit_repository_import,
    plan_repository_import,
)

__all__ = [
    "GitStore",
    "MergeArgument",
    "RepositoryMergeFramework",
    "build_merge_framework",
    "create_merge_commit",
    "PairState",
    "PartialArgumentationFramework",
    "enumerate_paf_completions",
    "merge_framework_edit_distance",
    "consensual_expand",
    "sum_merge_frameworks",
    "max_merge_frameworks",
    "leximax_merge_frameworks",
    "credulously_accepted_arguments",
    "skeptically_accepted_arguments",
    "summarize_merge_framework",
    "BranchStructuredSummary",
    "build_branch_structured_summary",
    "build_structured_merge_candidates",
    "RepositoryImportPlan",
    "RepositoryImportResult",
    "plan_repository_import",
    "commit_repository_import",
]
