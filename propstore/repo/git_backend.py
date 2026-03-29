"""Dulwich-backed git storage for knowledge repositories.

This is the single module where Dulwich is imported. All other modules
interact with git through the KnowledgeRepo wrapper, never Dulwich directly.

Design invariant: the git object store is the single source of truth.
The working tree is a materialized view for human inspection.

Moved from propstore/cli/git_backend.py in Phase 1 of the semantic merge
work. The old location is now a backward-compatibility shim.
"""
from __future__ import annotations

import re
import time
from pathlib import Path, PurePosixPath

import yaml
from dulwich.objects import Blob, Tree, Commit
from dulwich.repo import Repo

_CONCEPT_ID_RE = re.compile(r"^concept(\d+)$")


def _normalize_path(path: str | Path) -> str:
    """Normalize a path to forward-slash posix form."""
    return str(path).replace("\\", "/")

_GITIGNORE_CONTENT = """\
sidecar/
*.sqlite
*.sqlite-wal
*.sqlite-shm
*.hash
*.provenance
"""

_DEFAULT_AUTHOR = b"pks <pks@propstore>"


def _ref_get(refs, ref_name: bytes) -> bytes | None:
    """Safely get a ref value, returning None if it doesn't exist.

    Dulwich's DiskRefsContainer lacks a .get() method.
    """
    try:
        return refs[ref_name]
    except KeyError:
        return None


class KnowledgeRepo:
    """Git-backed knowledge repository wrapping a Dulwich Repo.

    All path arguments are repo-relative posix strings
    (e.g., ``"concepts/foo.yaml"``).
    """

    def __init__(self, dulwich_repo: Repo, root: Path) -> None:
        self._repo = dulwich_repo
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    # ── Lifecycle ────────────────────────────────────────────────────

    @classmethod
    def init(cls, root: Path) -> KnowledgeRepo:
        """Create a new git-backed knowledge repository."""
        root.mkdir(parents=True, exist_ok=True)
        dulwich_repo = Repo.init(str(root))
        kr = cls(dulwich_repo, root)
        # Commit .gitignore as the initial commit
        kr.commit_files({".gitignore": _GITIGNORE_CONTENT.encode("utf-8")}, "Initialize knowledge repository")
        kr.sync_worktree()
        return kr

    @classmethod
    def open(cls, root: Path) -> KnowledgeRepo:
        """Open an existing git-backed knowledge repository."""
        dulwich_repo = Repo(str(root))
        return cls(dulwich_repo, root)

    @staticmethod
    def is_repo(root: Path) -> bool:
        """Check if a directory contains a git repository."""
        return (root / ".git").is_dir()

    # ── Read ─────────────────────────────────────────────────────────

    def read_file(self, path: str | Path, commit: str | None = None) -> bytes:
        """Read a file from the git tree. Raises FileNotFoundError if missing."""
        path = _normalize_path(path)
        tree = self._get_tree(commit)
        parts = PurePosixPath(path).parts
        obj = self._walk_tree(tree, parts)
        if obj is None or not isinstance(obj, Blob):
            raise FileNotFoundError(path)
        return obj.data

    def list_dir(self, subdir: str | Path, commit: str | None = None) -> list[str]:
        """List file names in a subdirectory of the git tree."""
        subdir = _normalize_path(subdir)
        tree = self._get_tree(commit)
        if tree is None:
            return []
        parts = PurePosixPath(subdir).parts
        subtree = self._walk_tree(tree, parts)
        if subtree is None or not isinstance(subtree, Tree):
            return []
        return sorted(
            entry.path.decode("utf-8")
            for entry in subtree.items()
            if entry.mode & 0o100000  # regular file
        )

    # ── Write ────────────────────────────────────────────────────────

    def commit_files(
        self, changes: dict[str | Path, bytes], message: str, *, branch: str = "master"
    ) -> str:
        """Add/update files and commit. Returns the commit sha hex."""
        return self._commit(adds=changes, deletes=[], message=message, branch=branch)

    def commit_deletes(
        self, paths: list[str | Path], message: str, *, branch: str = "master"
    ) -> str:
        """Delete files and commit. Returns the commit sha hex."""
        return self._commit(adds={}, deletes=paths, message=message, branch=branch)

    def commit_batch(
        self,
        adds: dict[str | Path, bytes],
        deletes: list[str | Path],
        message: str,
        *,
        branch: str = "master",
    ) -> str:
        """Add/update and delete files in a single atomic commit."""
        return self._commit(adds=adds, deletes=deletes, message=message, branch=branch)

    # ── History ──────────────────────────────────────────────────────

    def log(self, max_count: int = 50, *, branch: str = "master") -> list[dict]:
        """Return recent commits as plain dicts, newest first.

        Walks from the tip of the named branch (default: master).
        Each entry includes a 'parents' list of hex SHA strings
        to support Backward Uniqueness verification (Bonanno 2007).
        """
        ref = f"refs/heads/{branch}".encode()
        tip = _ref_get(self._repo.refs, ref)
        if tip is None:
            # Fallback for HEAD-based access (backward compat)
            try:
                tip = self._repo.head()
            except KeyError:
                return []

        result: list[dict] = []
        walker = self._repo.get_walker(include=[tip], max_entries=max_count)
        for entry in walker:
            c = entry.commit
            result.append({
                "sha": c.id.decode("ascii"),
                "message": c.message.decode("utf-8", errors="replace").strip(),
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(c.commit_time)),
                "author": c.author.decode("utf-8", errors="replace"),
                "parents": [p.decode("ascii") for p in c.parents],
            })
        return result

    def head_sha(self) -> str | None:
        """Return the current HEAD commit sha as a hex string."""
        try:
            return self._repo.head().decode("ascii")
        except KeyError:
            return None

    def branch_sha(self, name: str) -> str | None:
        """Return the tip SHA for a named branch, or None if it doesn't exist."""
        ref = f"refs/heads/{name}".encode()
        sha = _ref_get(self._repo.refs, ref)
        if sha is None:
            return None
        return sha.decode("ascii")

    # ── Working tree ─────────────────────────────────────────────────

    def sync_worktree(self) -> None:
        """Materialize the HEAD tree onto the filesystem.

        Creates/updates files to match git state, removes files that
        are no longer in the tree (excluding .git/).
        """
        try:
            head = self._repo.head()
        except KeyError:
            return
        commit = self._repo[head]
        tree = self._repo[commit.tree]
        # Collect all paths in the git tree
        git_paths: set[str] = set()
        self._collect_tree_paths(tree, "", git_paths)

        # Write all git-tracked files
        for rel_path in git_paths:
            abs_path = self._root / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            blob = self._resolve_path(tree, PurePosixPath(rel_path).parts)
            if isinstance(blob, Blob):
                abs_path.write_bytes(blob.data)

        # Remove files that are on disk but not in git
        for disk_file in self._root.rglob("*"):
            if not disk_file.is_file():
                continue
            rel = disk_file.relative_to(self._root).as_posix()
            if rel.startswith(".git"):
                continue
            if rel not in git_paths:
                disk_file.unlink()

    # ── ID allocation ────────────────────────────────────────────────

    def next_concept_id(self) -> int:
        """Scan the git tree for the max concept ID and return max + 1."""
        try:
            names = self.list_dir("concepts")
        except (FileNotFoundError, KeyError):
            return 1
        max_id = 0
        for name in names:
            if not name.endswith(".yaml"):
                continue
            try:
                raw = self.read_file(f"concepts/{name}")
                data = yaml.safe_load(raw)
            except (FileNotFoundError, yaml.YAMLError):
                continue
            cid = (data or {}).get("id", "")
            if isinstance(cid, str):
                m = _CONCEPT_ID_RE.match(cid)
                if m:
                    max_id = max(max_id, int(m.group(1)))
        return max_id + 1

    # ── Diff / Show ──────────────────────────────────────────────────

    def diff_commits(
        self, commit1: str | None = None, commit2: str | None = None
    ) -> dict:
        """Compare two trees and return what changed.

        If commit1 is None, use HEAD.
        If commit2 is None, use the parent of commit1.

        Returns: {"added": [paths], "modified": [paths], "deleted": [paths]}
        """
        # Resolve commit1
        if commit1 is None:
            try:
                commit1 = self._repo.head().decode("ascii")
            except KeyError:
                return {"added": [], "modified": [], "deleted": []}

        # Resolve commit2 (parent of commit1)
        if commit2 is None:
            commit1_obj = self._repo[commit1.encode("ascii")]
            if commit1_obj.parents:
                commit2 = commit1_obj.parents[0].decode("ascii")
            else:
                # No parent — everything in commit1 is "added"
                commit2 = None

        # Flatten both trees
        tree1 = self._get_tree(commit1)
        entries1: dict[str, bytes] = {}
        if tree1 is not None:
            self._flatten_tree(tree1, "", entries1)

        entries2: dict[str, bytes] = {}
        if commit2 is not None:
            tree2 = self._get_tree(commit2)
            if tree2 is not None:
                self._flatten_tree(tree2, "", entries2)

        added = sorted(p for p in entries1 if p not in entries2)
        deleted = sorted(p for p in entries2 if p not in entries1)
        modified = sorted(
            p for p in entries1
            if p in entries2 and entries1[p] != entries2[p]
        )

        return {"added": added, "modified": modified, "deleted": deleted}

    def show_commit(self, sha: str) -> dict:
        """Return details about a single commit.

        Returns: {"sha": str, "message": str, "author": str, "time": str,
                  "added": [...], "modified": [...], "deleted": [...]}
        """
        commit_obj = self._repo[sha.encode("ascii")]
        info = {
            "sha": sha,
            "message": commit_obj.message.decode("utf-8", errors="replace").strip(),
            "author": commit_obj.author.decode("utf-8", errors="replace"),
            "time": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.gmtime(commit_obj.commit_time)
            ),
        }

        # Diff vs parent
        if commit_obj.parents:
            parent_sha = commit_obj.parents[0].decode("ascii")
        else:
            parent_sha = None

        diff = self.diff_commits(sha, parent_sha)
        info["added"] = diff["added"]
        info["modified"] = diff["modified"]
        info["deleted"] = diff["deleted"]
        return info

    # ── Internal ─────────────────────────────────────────────────────

    def _commit(
        self,
        adds: dict[str, bytes],
        deletes: list[str],
        message: str,
        branch: str = "master",
    ) -> str:
        """Build a new tree from the branch tip (if any), apply adds/deletes, commit.

        Parameterized by branch (Darwiche & Pearl 1997, C1-C4: each branch
        is an independent epistemic state). Parent is resolved from the
        named branch ref, not HEAD. HEAD symref is only set when
        branch == "master" (Bonanno 2007: BU preserved per branch).
        """
        store = self._repo.object_store
        branch_ref = f"refs/heads/{branch}".encode()

        # Get current tree from branch tip, or start empty
        tip_sha = _ref_get(self._repo.refs, branch_ref)
        if tip_sha is not None:
            parent_commit = self._repo[tip_sha]
            base_tree = self._repo[parent_commit.tree]
            parents = [tip_sha]
        else:
            base_tree = None
            parents = []

        # Build path -> blob mapping from base tree
        entries: dict[str, bytes] = {}  # path -> blob sha
        if base_tree is not None:
            self._flatten_tree(base_tree, "", entries)

        # Apply adds
        for path, content in adds.items():
            path = _normalize_path(path)
            blob = Blob.from_string(content)
            store.add_object(blob)
            entries[path] = blob.id

        # Apply deletes
        delete_set = {_normalize_path(p) for p in deletes}
        for path in delete_set:
            entries.pop(path, None)

        # Build tree hierarchy
        root_tree = self._build_tree_from_flat(entries, store)

        # Create commit
        commit = Commit()
        commit.tree = root_tree.id
        commit.author = _DEFAULT_AUTHOR
        commit.committer = _DEFAULT_AUTHOR
        commit.encoding = b"UTF-8"
        commit.message = message.encode("utf-8")
        now = int(time.time())
        commit.commit_time = now
        commit.author_time = now
        commit.commit_timezone = 0
        commit.author_timezone = 0
        commit.parents = parents
        store.add_object(commit)
        self._repo.refs[branch_ref] = commit.id
        # Only set HEAD symref when committing to master
        if branch == "master":
            if not self._repo.refs.get_symrefs().get(b"HEAD"):
                self._repo.refs.set_symbolic_ref(b"HEAD", b"refs/heads/master")

        return commit.id.decode("ascii")

    def _flatten_tree(
        self, tree: Tree, prefix: str, out: dict[str, bytes]
    ) -> None:
        """Recursively flatten a tree into path -> blob_sha mapping."""
        for entry in tree.items():
            name = entry.path.decode("utf-8")
            path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
            obj = self._repo[entry.sha]
            if isinstance(obj, Tree):
                self._flatten_tree(obj, path, out)
            elif isinstance(obj, Blob):
                out[path] = entry.sha

    def _build_tree_from_flat(
        self, entries: dict[str, bytes], store
    ) -> Tree:
        """Build a nested tree hierarchy from a flat path -> sha mapping."""
        # Group by first path component
        children: dict[str, list[tuple[str, bytes]]] = {}
        direct_blobs: list[tuple[str, bytes]] = []

        for path, sha in entries.items():
            parts = path.split("/", 1)
            if len(parts) == 1:
                direct_blobs.append((parts[0], sha))
            else:
                children.setdefault(parts[0], []).append((parts[1], sha))

        tree = Tree()
        # Add direct blobs
        for name, sha in sorted(direct_blobs):
            tree.add(name.encode("utf-8"), 0o100644, sha)

        # Recursively build subtrees
        for dirname in sorted(children):
            sub_entries = {rest: sha for rest, sha in children[dirname]}
            sub_tree = self._build_tree_from_flat(sub_entries, store)
            store.add_object(sub_tree)
            tree.add(dirname.encode("utf-8"), 0o040000, sub_tree.id)

        store.add_object(tree)
        return tree

    def _get_tree(self, commit: str | None = None) -> Tree | None:
        """Get the root tree for a commit (or HEAD)."""
        try:
            if commit is not None:
                commit_obj = self._repo[commit.encode("ascii")]
            else:
                head = self._repo.head()
                commit_obj = self._repo[head]
        except KeyError:
            return None
        return self._repo[commit_obj.tree]

    def _walk_tree(self, tree: Tree | None, parts: tuple[str, ...]):
        """Walk a tree by path parts, returning the final object or None."""
        if tree is None:
            return None
        obj = tree
        for part in parts:
            if not isinstance(obj, Tree):
                return None
            found = False
            for entry in obj.items():
                if entry.path.decode("utf-8") == part:
                    obj = self._repo[entry.sha]
                    found = True
                    break
            if not found:
                return None
        return obj

    def _resolve_path(self, tree: Tree, parts: tuple[str, ...]):
        """Alias for _walk_tree for clarity in sync_worktree."""
        return self._walk_tree(tree, parts)

    def _collect_tree_paths(
        self, tree: Tree, prefix: str, out: set[str]
    ) -> None:
        """Collect all file paths in a tree recursively."""
        for entry in tree.items():
            name = entry.path.decode("utf-8")
            path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
            obj = self._repo[entry.sha]
            if isinstance(obj, Tree):
                self._collect_tree_paths(obj, path, out)
            elif isinstance(obj, Blob):
                out.add(path)
