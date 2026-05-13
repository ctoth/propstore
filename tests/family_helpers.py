from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from quire.tree_path import (
    FilesystemTreePath,
    GitTreePath,
    TreePath,
    coerce_tree_path,
)
from quire.documents import (
    LoadedDocument,
    convert_document_value,
    decode_yaml_mapping,
)
from quire.git_store import GitStore

from propstore.claims import (
    LoadedClaimsFile,
    expand_loaded_claim_batch,
    load_claim_file,
)
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.families.claims.documents import ClaimsFileDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.stances import StanceDocument
from propstore.families.identity.claims import normalize_claim_file_payload
from propstore.families.identity.justifications import derive_justification_artifact_id
from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.registry import ClaimRef
from propstore.families.registry import JustificationRef, StanceRef
from propstore.families.concepts.stages import load_concepts
from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar as _build_sidecar
from propstore.storage import PROPSTORE_GIT_POLICY
from tests.git_store_helpers import is_store


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


def build_sidecar(repo_or_path: Repository | TreePath | Path, sidecar_path: Path, **kwargs):
    if isinstance(repo_or_path, Repository):
        repo = repo_or_path
        if repo.git is None:
            _init_git_without_sync(repo.root)
            repo = Repository(repo.root)
    elif isinstance(repo_or_path, GitTreePath):
        root = getattr(repo_or_path._store, "root", None)
        if root is None:
            raise TypeError("GitTreePath sidecar builds require a store with a filesystem root")
        kwargs.setdefault("commit_hash", repo_or_path._commit)
        repo = Repository(root)
    elif isinstance(repo_or_path, FilesystemTreePath):
        root = repo_or_path.concrete_path()
        _init_git_without_sync(root)
        repo = Repository(root)
    else:
        if not isinstance(repo_or_path, Path):
            raise TypeError("build_sidecar requires a Repository, Path, or concrete Quire tree path")
        _init_git_without_sync(repo_or_path)
        repo = Repository(repo_or_path)
    _materialize_claim_fixture_batches(repo)
    if kwargs.get("commit_hash") is None:
        _commit_worktree(repo)
    return _build_sidecar(repo, sidecar_path, **kwargs)


def claim_artifact_commit_payloads(
    repo: Repository,
    batch_payload: Mapping[str, object],
    *,
    source: str,
) -> dict[str, bytes]:
    normalized, _ = normalize_claim_file_payload(batch_payload)
    source_path = repo.root / source
    batch = LoadedDocument(
        filename=source_path.name,
        artifact_path=source_path,
        store_root=repo.root,
        document=convert_document_value(
            normalized,
            ClaimsFileDocument,
            source=source,
        ),
    )
    payloads: dict[str, bytes] = {}
    for loaded in expand_loaded_claim_batch(batch):
        claim = loaded.document
        artifact_id = claim.artifact_id
        if artifact_id is None:
            raise ValueError(f"{source}: normalized claim is missing artifact_id")
        ref = ClaimRef(artifact_id)
        artifact_path = repo.families.claims.address(ref).require_path()
        payloads[artifact_path] = (
            repo.families.claims.render(claim) + "\n"
        ).encode("utf-8")
    return payloads


def stance_artifact_commit_payload(
    repo: Repository,
    stance_payload: Mapping[str, object],
) -> dict[str, bytes]:
    artifact_id = derive_stance_artifact_id(dict(stance_payload))
    document = convert_document_value(
        stance_payload,
        StanceDocument,
        source=artifact_id,
    )
    path = repo.families.stances.address(StanceRef(artifact_id)).require_path()
    return {
        path: (repo.families.stances.render(document) + "\n").encode("utf-8"),
    }


def justification_artifact_commit_payload(
    repo: Repository,
    justification_payload: Mapping[str, object],
) -> dict[str, bytes]:
    artifact_id = derive_justification_artifact_id(dict(justification_payload))
    document = convert_document_value(
        justification_payload,
        JustificationDocument,
        source=artifact_id,
    )
    path = repo.families.justifications.address(JustificationRef(artifact_id)).require_path()
    return {
        path: (repo.families.justifications.render(document) + "\n").encode("utf-8"),
    }


def _load_claim_fixture(
    entry: TreePath,
    *,
    knowledge_root: TreePath,
) -> tuple[LoadedClaimsFile, ...]:
    data = decode_yaml_mapping(entry.read_bytes(), source=entry.as_posix())
    if isinstance(data.get("claims"), list):
        normalized, _ = normalize_claim_file_payload(data)
        batch = LoadedDocument(
            filename=entry.name,
            artifact_path=entry,
            store_root=knowledge_root,
            document=convert_document_value(
                normalized,
                ClaimsFileDocument,
                source=entry.as_posix(),
            ),
        )
        return expand_loaded_claim_batch(batch)
    return (load_claim_file(entry, knowledge_root=knowledge_root),)


def _materialize_claim_fixture_batches(repo: Repository) -> None:
    claims_dir = repo.root / "claims"
    if not claims_dir.is_dir():
        return
    for path in sorted(claims_dir.glob("*.yaml")):
        data = decode_yaml_mapping(path.read_bytes(), source=path.as_posix())
        if not isinstance(data.get("claims"), list):
            continue
        normalized, _ = normalize_claim_file_payload(data)
        batch = LoadedDocument(
            filename=path.name,
            artifact_path=path,
            store_root=repo.root,
            document=convert_document_value(
                normalized,
                ClaimsFileDocument,
                source=path.as_posix(),
            ),
        )
        for loaded in expand_loaded_claim_batch(batch):
            claim = loaded.document
            artifact_id = claim.artifact_id
            if artifact_id is None:
                raise ValueError(f"{path.as_posix()}: normalized claim is missing artifact_id")
            ref = ClaimRef(artifact_id)
            artifact_path = repo.root / repo.families.claims.address(ref).require_path()
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                repo.families.claims.render(claim) + "\n",
                encoding="utf-8",
            )
        path.unlink()


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
        if rel_text.startswith("sidecar/") or rel_text.endswith((".sqlite", ".sqlite-wal", ".sqlite-shm", ".hash")):
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
