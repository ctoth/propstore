from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from propstore.artifacts.codecs import convert_document, decode_document, encode_document, render_document
from propstore.artifacts.transaction import ArtifactTransaction, normalized_path
from propstore.artifacts.types import ArtifactContext, ArtifactFamily, ArtifactHandle, ResolvedArtifact, TDoc, TRef
from propstore.repo.branch import branch_head

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


class ArtifactStore:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    @property
    def repo(self) -> Repository:
        return self._repo

    def resolve(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ResolvedArtifact:
        resolved = family.resolve_ref(self._repo, ref)
        if commit is None:
            return resolved
        return ResolvedArtifact(branch=resolved.branch, relpath=resolved.relpath, commit=commit)

    def ref_from_path(
        self,
        family: ArtifactFamily[TRef, TDoc],
        path: str | Path,
    ) -> TRef:
        if family.ref_from_path is None:
            raise TypeError(f"{family.name} does not support path-derived refs")
        return family.ref_from_path(path)

    def ref_from_loaded(
        self,
        family: ArtifactFamily[TRef, TDoc],
        loaded: object,
    ) -> TRef:
        if family.ref_from_loaded is None:
            raise TypeError(f"{family.name} does not support loaded-object refs")
        return family.ref_from_loaded(loaded)

    def coerce(
        self,
        family: ArtifactFamily[TRef, TDoc],
        payload: object,
        *,
        source: str,
    ) -> TDoc:
        return convert_document(payload, family.doc_type, source=source)

    def render(self, document: object) -> str:
        return render_document(document)

    def load(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc | None:
        if self._repo.git is None:
            raise ValueError("artifact operations require a git-backed repository")
        resolved = self.resolve(family, ref, commit=commit)
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

    def handle(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ArtifactHandle[TRef, TDoc] | None:
        document = self.load(family, ref, commit=commit)
        if document is None:
            return None
        return ArtifactHandle(
            family=family,
            ref=ref,
            resolved=self.resolve(family, ref, commit=commit),
            document=document,
        )

    def require_handle(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ArtifactHandle[TRef, TDoc]:
        handle = self.handle(family, ref, commit=commit)
        if handle is None:
            resolved = self.resolve(family, ref, commit=commit)
            raise FileNotFoundError(f"{family.name}: {resolved.branch}:{normalized_path(resolved.relpath)}")
        return handle

    def require(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc:
        return self.require_handle(family, ref, commit=commit).document

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
        resolved = self.resolve(family, ref)
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

    def move(
        self,
        family: ArtifactFamily[TRef, TDoc],
        old_ref: TRef,
        new_ref: TRef,
        doc: TDoc,
        *,
        message: str,
        branch: str | None = None,
    ) -> str:
        transaction = self.transact(message=message, branch=branch)
        transaction.move(family, old_ref, new_ref, doc)
        return transaction.commit()

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
        resolved = self.resolve(family, ref)
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
