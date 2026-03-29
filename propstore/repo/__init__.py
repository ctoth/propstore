"""Repository layer for propstore — git-backed knowledge storage.

Re-exports KnowledgeRepo from the canonical location.
"""
from propstore.repo.git_backend import KnowledgeRepo

__all__ = ["KnowledgeRepo"]
