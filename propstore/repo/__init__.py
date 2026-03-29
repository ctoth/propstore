"""Repository layer for propstore — git-backed knowledge storage.

Re-exports KnowledgeRepo and merge primitives from canonical locations.
"""
from propstore.repo.git_backend import KnowledgeRepo
from propstore.repo.merge_classifier import MergeClassification, MergeItem, classify_merge
from propstore.repo.merge_commit import create_merge_commit
from propstore.repo.branch_reasoning import (
    make_branch_assumption,
    branch_nogoods_from_merge,
    inject_branch_stances,
)
from propstore.repo.ic_merge import (
    MergeOperator,
    sigma_merge,
    max_merge,
    gmax_merge,
    ic_merge,
    claim_distance,
)

__all__ = [
    "KnowledgeRepo",
    "MergeClassification",
    "MergeItem",
    "classify_merge",
    "create_merge_commit",
    "make_branch_assumption",
    "branch_nogoods_from_merge",
    "inject_branch_stances",
    "MergeOperator",
    "sigma_merge",
    "max_merge",
    "gmax_merge",
    "ic_merge",
    "claim_distance",
]
