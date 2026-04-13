from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.artifacts.codecs import decode_document, encode_document
from propstore.artifacts.transaction import ArtifactTransaction, normalized_path
from propstore.artifacts.types import ArtifactContext, ArtifactFamily, TDoc, TRef
from propstore.repo.branch import branch_head

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


class ArtifactStore:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    @property
    def repo(self) -> Repository:
        return self._repo

    def load(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc | None:
        if self._repo.git is None:
            raise ValueError("artifact operations require a git-backed repository")
        resolved = family.resolve_ref(self._repo, ref)
        target_commit = commit or resolved.commit
        if target_commit is None:
            target_commit = branch_head(self._repo.git, resolved.branch)
            if target_commit is None:
                return None
        try:
            raw = self._repo.git.read_file(resolved.relpath, commit=target_commit)
        except FileNotFoundError:
            return None
        return decode_document(
            raw,
            family.doc_type,
            source=f"{resolved.branch}:{normalized_path(resolved.relpath)}",
        )

    def require(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc:
        loaded = self.load(family, ref, commit=commit)
        if loaded is None:
            resolved = family.resolve_ref(self._repo, ref)
            raise FileNotFoundError(f"{family.name}: {resolved.branch}:{normalized_path(resolved.relpath)}")
        return loaded

    def save(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        doc: TDoc,
        *,
        message: str,
        branch: str | None = None,
    ) -> str:
        if self._repo.git is None:
            raise ValueError("artifact operations require a git-backed repository")
        resolved = family.resolve_ref(self._repo, ref)
        target_branch = branch or resolved.branch
        context = ArtifactContext(
            repo=self._repo,
            ref=ref,
            branch=target_branch,
            relpath=resolved.relpath,
        )
        normalized = doc
        if family.normalize_for_write is not None:
            normalized = family.normalize_for_write(context, normalized, self)
        if family.validate_for_write is not None:
            family.validate_for_write(context, normalized, self)
        return self._repo.git.commit_batch(
            adds={normalized_path(resolved.relpath): encode_document(normalized)},
            deletes=[],
            message=message,
            branch=target_branch,
        )

    def delete(
        self,
        family: ArtifactFamily[TRef, object],
        ref: TRef,
        *,
        message: str,
        branch: str | None = None,
    ) -> str:
        if self._repo.git is None:
            raise ValueError("artifact operations require a git-backed repository")
        resolved = family.resolve_ref(self._repo, ref)
        target_branch = branch or resolved.branch
        return self._repo.git.commit_batch(
            adds={},
            deletes=[normalized_path(resolved.relpath)],
            message=message,
            branch=target_branch,
        )

    def list(
        self,
        family: ArtifactFamily[TRef, TDoc],
        *,
        branch: str | None = None,
        commit: str | None = None,
    ) -> list[TRef]:
        if family.list_refs is None:
            raise TypeError(f"{family.name} does not support listing")
        return family.list_refs(self._repo, branch, commit)

    def transact(
        self,
        *,
        message: str,
        branch: str | None = None,
    ) -> ArtifactTransaction:
        return ArtifactTransaction(repo=self._repo, message=message, branch=branch)
