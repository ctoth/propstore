"""Git-backed storage layer for propstore."""
from propstore.storage.git_policy import (
    init_git_store,
    init_memory_git_store,
    is_git_repo,
    open_git_store,
)

__all__ = [
    "init_git_store",
    "init_memory_git_store",
    "is_git_repo",
    "open_git_store",
]
