"""Branch operations for propstore knowledge repositories.

All functions take a GitStore as first argument rather than
being methods — branches are operations ON a repo, not OF a repo.

Literature grounding:
- Bonanno 2007, claim 9: Backward Uniqueness — each branch has
  linear history (single parent per commit).
- Darwiche & Pearl 1997, C1-C4: each branch is an independent
  epistemic state for iterated belief revision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.storage.git_backend import GitStore


@dataclass(frozen=True)
class BranchInfo:
    """Metadata about a branch.

    Attributes:
        name: Branch name (e.g. "paper/foo", "main").
        tip_sha: Hex SHA of the branch tip commit.
        kind: Inferred from name prefix — "paper", "source", "agent",
              "hypothesis", or "workspace".
    """
    name: str
    tip_sha: str
    kind: str  # "paper", "source", "agent", "hypothesis", "workspace"
    parent_branch: str = ""
    created_at: int = 0


def _detect_kind(name: str) -> str:
    """Infer branch kind from naming convention prefix.

    Propstore spec: paper/{slug}, source/{slug}, agent/{run_id}, hypothesis/{name}.
    Anything else is "workspace".
    """
    for prefix in ("paper/", "source/", "agent/", "hypothesis/"):
        if name.startswith(prefix):
            return prefix.rstrip("/")
    return "workspace"


def create_branch(kr: GitStore, name: str, source_commit: str | None = None) -> str:
    """Create a branch pointing at source_commit (default: current HEAD tip).

    Returns the tip SHA of the new branch.
    Raises ValueError if the branch already exists.
    """
    return kr.create_branch(name, source_commit=source_commit)


def delete_branch(kr: GitStore, name: str) -> None:
    """Delete a branch. Raises ValueError for the current HEAD branch.

    The checked-out branch must never be deleted
    (analogous to AGM's requirement that the knowledge base always
    exists — Alchourrón et al. 1985).
    """
    kr.delete_branch(name)


def list_branches(kr: GitStore) -> list[BranchInfo]:
    """List all branches with metadata.

    Returns BranchInfo for every ref under refs/heads/.
    """
    result: list[BranchInfo] = []
    for branch in kr.list_branches():
        result.append(BranchInfo(
            name=branch.name,
            tip_sha=branch.tip_sha,
            kind=_detect_kind(branch.name),
            parent_branch=branch.parent_branch,
            created_at=branch.created_at,
        ))
    return result


def branch_head(kr: GitStore, name: str) -> str | None:
    """Return tip SHA for a branch, or None if branch doesn't exist."""
    return kr.branch_sha(name)


def merge_base(kr: GitStore, branch_a: str, branch_b: str) -> str:
    """Find common ancestor of two branches by walking parents.

    Returns a Git-like best common ancestor: a common ancestor that is not
    itself an ancestor of any other common ancestor. If multiple best common
    ancestors remain, choose the nearest one by shortest-path distance from the
    two tips, with lexical SHA tie-breaking for determinism.

    Konieczny & Pino Pérez 2002: IC merging requires identifying the
    common knowledge base from which branches diverged.
    """
    return kr.merge_base(branch_a, branch_b)
