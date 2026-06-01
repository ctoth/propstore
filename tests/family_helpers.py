from __future__ import annotations

from pathlib import Path

from quire.tree_path import (
    FilesystemTreePath,
    GitTreePath,
    TreePath,
    coerce_tree_path,
)
from quire.git_store import GitStore

from propstore.claims import (
    LoadedClaimsFile,
)
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.families.concepts.stages import load_concepts
from propstore.repository import Repository
from propstore.compiler.workflows import (
    build_repository_world_store,
    write_repository_world_store as _write_repository_world_store,
)
from propstore.storage import PROPSTORE_GIT_POLICY
from tests.git_store_helpers import is_store
from quire.derived_store import DerivedStoreHandle


def load_claim_files(claims_dir: TreePath | Path) -> list[LoadedClaimsFile]:
    tree = coerce_tree_path(claims_dir)
    if not tree.exists():
        return []
    files: list[LoadedClaimsFile] = []
    for entry in tree.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            files.extend(_load_claim_fixture(entry, knowledge_root=tree.parent))
    return files


def build_compilation_context_from_paths(
    concepts_dir: TreePath | Path,
    forms_dir: TreePath | Path,
    *,
    claim_files: list[LoadedClaimsFile] | None = None,
):
    return build_compilation_context_from_loaded(
        load_concepts(coerce_tree_path(concepts_dir)),
        forms_dir=forms_dir,
        claim_files=claim_files,
    )


def build_sidecar(
    repo_or_path: Repository | TreePath | Path, sidecar_path: Path, **kwargs
):
    if isinstance(repo_or_path, Repository):
        repo = repo_or_path
        if repo.git is None:
            _init_git_without_sync(repo.root)
            repo = Repository(repo.root)
    elif isinstance(repo_or_path, GitTreePath):
        root = getattr(repo_or_path._store, "root", None)
        if root is None:
            raise TypeError(
                "GitTreePath sidecar builds require a store with a filesystem root"
            )
        kwargs.setdefault("commit_hash", repo_or_path._commit)
        repo = Repository(root)
    elif isinstance(repo_or_path, FilesystemTreePath):
        root = repo_or_path.concrete_path()
        _init_git_without_sync(root)
        repo = Repository(root)
    else:
        if not isinstance(repo_or_path, Path):
            raise TypeError(
                "build_sidecar requires a Repository, Path, or concrete Quire tree path"
            )
        _init_git_without_sync(repo_or_path)
        repo = Repository(repo_or_path)
    _materialize_claim_fixture_batches(repo)
    if kwargs.get("commit_hash") is None:
        _commit_worktree(repo)
    return _write_repository_world_store(repo, sidecar_path, **kwargs)


def materialized_world_store(
    repo: Repository,
    *,
    force: bool = False,
    **kwargs,
) -> DerivedStoreHandle:
    if repo.git is None:
        _init_git_without_sync(repo.root)
        for cached_name in ("git", "_family_store", "families", "snapshot"):
            repo.__dict__.pop(cached_name, None)
    _materialize_claim_fixture_batches(repo)
    if kwargs.get("commit_hash") is None:
        _commit_worktree(repo)
    handle, _ = build_repository_world_store(repo, force=force, **kwargs)
    return handle


def materialized_world_store_path(
    repo: Repository,
    *,
    force: bool = False,
    **kwargs,
) -> Path:
    return materialized_world_store(repo, force=force, **kwargs).path


def world_query_from_sqlite_path(sqlite_path: Path):
    from propstore.world import WorldQuery

    return WorldQuery(
        derived_store=DerivedStoreHandle(
            projection_id="propstore.world.test",
            source_commit="test",
            content_hash="test",
            cache_key="test",
            path=sqlite_path,
        )
    )


def _init_git_without_sync(root: Path) -> None:
    if not is_store(root):
        GitStore.init(root, policy=PROPSTORE_GIT_POLICY)


def _commit_worktree(repo: Repository, message: str = "Update test knowledge") -> str:
    git = repo.git
    if git is None:
        raise TypeError("test sidecar builds require a git-backed repository")
    adds: dict[str | Path, bytes] = {}
    head = git.head_sha()
    changed = head is None
    for path in sorted(repo.root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo.root)
        if ".git" in rel.parts:
            continue
        rel_text = rel.as_posix()
        if rel_text.startswith("sidecar/") or rel_text.endswith(
            (".sqlite", ".sqlite-wal", ".sqlite-shm", ".hash")
        ):
            continue
        content = path.read_bytes()
        adds[rel_text] = content
        if not changed:
            try:
                changed = git.read_file(rel_text, commit=head) != content
            except FileNotFoundError:
                changed = True
    if not changed and head is not None:
        return head
    return git.commit_batch(adds=adds, deletes=(), message=message)
