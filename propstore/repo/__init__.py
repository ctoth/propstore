"""Repository layer for propstore — git-backed knowledge storage.

Re-exports KnowledgeRepo and merge primitives from canonical locations.
"""
from propstore.repo.git_backend import KnowledgeRepo
from propstore.repo.merge_classifier import MergeClassification, MergeItem, classify_merge
from propstore.repo.merge_commit import create_merge_commit

__all__ = [
    "KnowledgeRepo",
    "MergeClassification",
    "MergeItem",
    "classify_merge",
    "create_merge_commit",
]
