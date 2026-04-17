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

import time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.storage.git_backend import _commit_object, _ref_delete, _ref_get, _ref_set

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
    ref = f"refs/heads/{name}".encode()
    if _ref_get(kr._repo.refs, ref):
        raise ValueError(f"Branch {name!r} already exists")

    parent_branch = ""
    if source_commit is None:
        current_branch = kr.current_branch_name()
        if current_branch is not None:
            current_ref = _ref_get(kr._repo.refs, f"refs/heads/{current_branch}".encode())
            if current_ref is None:
                raise ValueError(f"Current branch {current_branch!r} has no tip")
            sha_bytes = current_ref
            parent_branch = current_branch
        else:
            head_sha = kr.head_sha()
            if head_sha is None:
                raise ValueError("Repository has no commits")
            sha_bytes = head_sha.encode("ascii")
    else:
        sha_bytes = source_commit.encode("ascii")

    _ref_set(kr._repo.refs, ref, sha_bytes)
    kr._branch_meta[name] = {
        "parent_branch": parent_branch,
        "created_at": int(time.time()),
    }
    return sha_bytes.decode("ascii")


def delete_branch(kr: GitStore, name: str) -> None:
    """Delete a branch. Raises ValueError for the current HEAD branch.

    The checked-out branch must never be deleted
    (analogous to AGM's requirement that the knowledge base always
    exists — Alchourrón et al. 1985).
    """
    if kr.current_branch_name() == name:
        raise ValueError("Cannot delete current HEAD branch")
    ref = f"refs/heads/{name}".encode()
    if _ref_get(kr._repo.refs, ref) is None:
        raise ValueError(f"Branch {name!r} does not exist")
    _ref_delete(kr._repo.refs, ref)


def list_branches(kr: GitStore) -> list[BranchInfo]:
    """List all branches with metadata.

    Returns BranchInfo for every ref under refs/heads/.
    """
    result: list[BranchInfo] = []
    prefix = b"refs/heads/"
    all_refs = kr._repo.refs.as_dict()
    for ref_bytes, sha_bytes in sorted(all_refs.items()):
        if not ref_bytes.startswith(prefix):
            continue
        name = ref_bytes[len(prefix):].decode("utf-8")
        tip_sha = sha_bytes.decode("ascii")
        meta = kr._branch_meta.get(name, {})
        parent_branch = meta.get("parent_branch", "")
        created_at = meta.get("created_at", 0)
        result.append(BranchInfo(
            name=name,
            tip_sha=tip_sha,
            kind=_detect_kind(name),
            parent_branch=parent_branch if isinstance(parent_branch, str) else "",
            created_at=created_at if isinstance(created_at, int) else 0,
        ))
    return result


def branch_head(kr: GitStore, name: str) -> str | None:
    """Return tip SHA for a branch, or None if branch doesn't exist."""
    ref = f"refs/heads/{name}".encode()
    sha_bytes = _ref_get(kr._repo.refs, ref)
    if sha_bytes is None:
        return None
    return sha_bytes.decode("ascii")


def _ancestor_distances(kr: GitStore, start_sha: str) -> dict[str, int]:
    """Return shortest-path distances from a commit to all of its ancestors."""
    distances: dict[str, int] = {start_sha: 0}
    queue: deque[str] = deque([start_sha])
    while queue:
        current = queue.popleft()
        current_distance = distances[current]
        commit_obj = _commit_object(kr._repo, current.encode("ascii"))
        for parent in commit_obj.parents:
            parent_sha = parent.decode("ascii")
            next_distance = current_distance + 1
            previous = distances.get(parent_sha)
            if previous is None or next_distance < previous:
                distances[parent_sha] = next_distance
                queue.append(parent_sha)
    return distances


def merge_base(kr: GitStore, branch_a: str, branch_b: str) -> str:
    """Find common ancestor of two branches by walking parents.

    Returns a Git-like best common ancestor: a common ancestor that is not
    itself an ancestor of any other common ancestor. If multiple best common
    ancestors remain, choose the nearest one by shortest-path distance from the
    two tips, with lexical SHA tie-breaking for determinism.

    Konieczny & Pino Pérez 2002: IC merging requires identifying the
    common knowledge base from which branches diverged.
    """
    sha_a = branch_head(kr, branch_a)
    sha_b = branch_head(kr, branch_b)
    if sha_a is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if sha_b is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    # Same tip — trivial case
    if sha_a == sha_b:
        return sha_a

    distances_a = _ancestor_distances(kr, sha_a)
    distances_b = _ancestor_distances(kr, sha_b)
    common_ancestors = set(distances_a) & set(distances_b)
    if not common_ancestors:
        raise ValueError(f"No common ancestor between {branch_a!r} and {branch_b!r}")

    ancestor_cache = {
        ancestor_sha: _ancestor_distances(kr, ancestor_sha)
        for ancestor_sha in common_ancestors
    }
    best_common_ancestors = {
        candidate
        for candidate in common_ancestors
        if not any(
            other != candidate and candidate in ancestor_cache[other]
            for other in common_ancestors
        )
    }

    return min(
        best_common_ancestors,
        key=lambda sha: (
            max(distances_a[sha], distances_b[sha]),
            distances_a[sha] + distances_b[sha],
            sha,
        ),
    )
