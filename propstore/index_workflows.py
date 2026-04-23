"""Index-reset workflow for the propstore CLI.

Rewrites the working git index so it matches HEAD, discarding any
staged additions or deletions that might linger from previous git
operations. Used by the ``pks index reset`` CLI surface to recover
from the phantom-deletion pattern documented in
``feedback_propstore_git_backend.md``.

Quire's ``GitStore.sync_worktree`` only materializes files on disk —
it does not touch the dulwich index. When a user interleaves
hand-authored ``git add`` with ``pks source promote``, the index can
retain stale deletion entries. A plain ``git commit`` afterwards then
silently wipes files. Resetting the index to HEAD is the simplest
mitigation.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.repository import Repository


class IndexWorkflowError(Exception):
    """Raised when the index reset cannot complete."""


@dataclass(frozen=True)
class IndexResetReport:
    head_sha: str
    cleared_entries: int


def reset_index(repo: Repository) -> IndexResetReport:
    """Rewrite the git index to match the current HEAD tree.

    Returns the HEAD sha and the number of entries that were present in
    the index before the reset (including any that already matched
    HEAD). This number is observational only — callers should not rely
    on it to tell "phantom" entries from matching ones.
    """
    git = getattr(repo, "git", None)
    if git is None:
        raise IndexWorkflowError("repository has no git backend")

    dulwich_repo = getattr(git, "_repo", None)
    if dulwich_repo is None:
        raise IndexWorkflowError("git backend has no underlying dulwich repository")

    head_sha: str | None
    try:
        head_bytes = dulwich_repo.head()
    except KeyError as exc:
        raise IndexWorkflowError("repository has no HEAD commit") from exc
    head_sha = head_bytes.decode("ascii") if isinstance(head_bytes, bytes) else str(head_bytes)

    commit = dulwich_repo.object_store[head_bytes]
    tree_id = commit.tree

    try:
        index = dulwich_repo.open_index()
    except Exception as exc:  # noqa: BLE001 — dulwich surfaces a bare Exception here
        raise IndexWorkflowError(f"cannot open index: {exc}") from exc

    prior_entries = sum(1 for _ in index)

    # Rebuild the index to exactly match the HEAD tree — ignoring
    # whatever was staged before. This is equivalent to
    # ``git read-tree --reset HEAD``.
    from dulwich.index import build_index_from_tree

    build_index_from_tree(
        dulwich_repo.path,
        dulwich_repo.index_path(),
        dulwich_repo.object_store,
        tree_id,
    )

    return IndexResetReport(head_sha=head_sha, cleared_entries=prior_entries)
