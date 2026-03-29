"""Branch operations for propstore knowledge repositories.

All functions take a KnowledgeRepo as first argument rather than
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

from propstore.repo.git_backend import _ref_get

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


@dataclass(frozen=True)
class BranchInfo:
    """Metadata about a branch.

    Attributes:
        name: Branch name (e.g. "paper/foo", "master").
        tip_sha: Hex SHA of the branch tip commit.
        kind: Inferred from name prefix — "paper", "agent",
              "hypothesis", or "workspace".
    """
    name: str
    tip_sha: str
    kind: str  # "paper", "agent", "hypothesis", "workspace"


def _detect_kind(name: str) -> str:
    """Infer branch kind from naming convention prefix.

    Propstore spec: paper/{slug}, agent/{run_id}, hypothesis/{name}.
    Anything else is "workspace".
    """
    for prefix in ("paper/", "agent/", "hypothesis/"):
        if name.startswith(prefix):
            return prefix.rstrip("/")
    return "workspace"


def create_branch(kr: KnowledgeRepo, name: str, source_commit: str | None = None) -> str:
    """Create a branch pointing at source_commit (default: master tip).

    Returns the tip SHA of the new branch.
    Raises ValueError if the branch already exists.
    """
    ref = f"refs/heads/{name}".encode()
    if _ref_get(kr._repo.refs, ref):
        raise ValueError(f"Branch {name!r} already exists")

    if source_commit is None:
        # Default to master tip
        master_ref = _ref_get(kr._repo.refs, b"refs/heads/master")
        if master_ref is None:
            raise ValueError("No master branch — repository has no commits")
        sha_bytes = master_ref
    else:
        sha_bytes = source_commit.encode("ascii")

    kr._repo.refs[ref] = sha_bytes
    return sha_bytes.decode("ascii")


def delete_branch(kr: KnowledgeRepo, name: str) -> None:
    """Delete a branch. Raises ValueError for 'master'.

    Master is the integration branch and must never be deleted
    (analogous to AGM's requirement that the knowledge base always
    exists — Alchourrón et al. 1985).
    """
    if name == "master":
        raise ValueError("Cannot delete master branch")
    ref = f"refs/heads/{name}".encode()
    if _ref_get(kr._repo.refs, ref) is None:
        raise ValueError(f"Branch {name!r} does not exist")
    del kr._repo.refs[ref]


def list_branches(kr: KnowledgeRepo) -> list[BranchInfo]:
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
        result.append(BranchInfo(name=name, tip_sha=tip_sha, kind=_detect_kind(name)))
    return result


def branch_head(kr: KnowledgeRepo, name: str) -> str | None:
    """Return tip SHA for a branch, or None if branch doesn't exist."""
    ref = f"refs/heads/{name}".encode()
    sha_bytes = _ref_get(kr._repo.refs, ref)
    if sha_bytes is None:
        return None
    return sha_bytes.decode("ascii")


def merge_base(kr: KnowledgeRepo, branch_a: str, branch_b: str) -> str:
    """Find common ancestor of two branches by walking parents.

    Uses BFS from both branch tips simultaneously. For the same-branch
    case, returns the branch tip.

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

    # BFS from both sides: collect ancestors of each, find first overlap
    ancestors_a: set[str] = set()
    ancestors_b: set[str] = set()
    queue_a: list[str] = [sha_a]
    queue_b: list[str] = [sha_b]

    while queue_a or queue_b:
        if queue_a:
            current = queue_a.pop(0)
            if current in ancestors_b:
                return current
            if current not in ancestors_a:
                ancestors_a.add(current)
                commit_obj = kr._repo[current.encode("ascii")]
                for p in commit_obj.parents:
                    parent_sha = p.decode("ascii")
                    if parent_sha not in ancestors_a:
                        queue_a.append(parent_sha)

        if queue_b:
            current = queue_b.pop(0)
            if current in ancestors_a:
                return current
            if current not in ancestors_b:
                ancestors_b.add(current)
                commit_obj = kr._repo[current.encode("ascii")]
                for p in commit_obj.parents:
                    parent_sha = p.decode("ascii")
                    if parent_sha not in ancestors_b:
                        queue_b.append(parent_sha)

    raise ValueError(f"No common ancestor between {branch_a!r} and {branch_b!r}")
