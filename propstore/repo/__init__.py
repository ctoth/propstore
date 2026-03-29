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

__all__ = [
    "KnowledgeRepo",
    "MergeClassification",
    "MergeItem",
    "classify_merge",
    "create_merge_commit",
    "make_branch_assumption",
    "branch_nogoods_from_merge",
    "inject_branch_stances",
]
