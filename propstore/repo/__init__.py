"""Repository layer for propstore.

Re-exports the canonical git-backed storage surface plus merge primitives.
For IC-merge, the assignment-level ``solve_ic_merge`` path is the public API.
"""
from propstore.repo.git_backend import KnowledgeRepo
from propstore.repo.merge_classifier import (
    MergeArgument,
    RepoMergeFramework,
    build_merge_framework,
)
from propstore.repo.merge_commit import create_merge_commit
from propstore.repo.branch_reasoning import (
    make_branch_assumption,
    branch_nogoods_from_merge,
    inject_branch_stances,
)
from propstore.repo.merge_framework import (
    PairState,
    PartialArgumentationFramework,
    enumerate_paf_completions,
    merge_framework_edit_distance,
)
from propstore.repo.paf_merge import (
    consensual_expand,
    sum_merge_frameworks,
    max_merge_frameworks,
    leximax_merge_frameworks,
)
from propstore.repo.paf_queries import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)
from propstore.repo.merge_report import summarize_merge_framework
from propstore.repo.structured_merge import (
    BranchStructuredSummary,
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from propstore.repo.ic_merge import (
    ICMergeProblem,
    ICMergeResult,
    MergeOperator,
    claim_distance,
    solve_ic_merge,
)

__all__ = [
    "KnowledgeRepo",
    "MergeArgument",
    "RepoMergeFramework",
    "build_merge_framework",
    "create_merge_commit",
    "make_branch_assumption",
    "branch_nogoods_from_merge",
    "inject_branch_stances",
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
    "ICMergeProblem",
    "ICMergeResult",
    "MergeOperator",
    "solve_ic_merge",
    "claim_distance",
]
