from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.artifacts.codecs import convert_document, document_to_payload, encode_document
from propstore.artifacts.types import ArtifactFamily, ArtifactContext, ResolvedArtifact, TDoc, TRef

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


@dataclass
class ArtifactTransaction:
    repo: Repository
    message: str
    branch: str | None = None
    _adds: dict[str, bytes] = field(default_factory=dict)
    _deletes: set[str] = field(default_factory=set)
    _commit_sha: str | None = None

    @property
    def commit_sha(self) -> str | None:
        return self._commit_sha

    def coerce(self, family: ArtifactFamily[TRef, TDoc], payload: object, *, source: str) -> TDoc:
        return convert_document(payload, family.doc_type, source=source)

    def payload(self, document: object) -> object:
        return document_to_payload(document)

    def __enter__(self) -> ArtifactTransaction:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None and self._commit_sha is None and (self._adds or self._deletes):
            self.commit()

    def save(self, family: ArtifactFamily[TRef, TDoc], ref: TRef, doc: TDoc) -> None:
        self._ensure_open()
        branch, resolved = self._resolved_target(family, ref)
        context = ArtifactContext(repo=self.repo, ref=ref, branch=branch, relpath=resolved.relpath)
        normalized = doc
        if family.normalize_for_write is not None:
            normalized = family.normalize_for_write(context, normalized, self)
        if family.validate_for_write is not None:
            family.validate_for_write(context, normalized, self)
        relpath = normalized_path(resolved.relpath)
        self._adds[relpath] = encode_document(normalized)
        self._deletes.discard(relpath)

    def delete(self, family: ArtifactFamily[TRef, object], ref: TRef) -> None:
        self._ensure_open()
        _, resolved = self._resolved_target(family, ref)
        relpath = normalized_path(resolved.relpath)
        self._deletes.add(relpath)
        self._adds.pop(relpath, None)

    def move(self, family: ArtifactFamily[TRef, TDoc], old_ref: TRef, new_ref: TRef, doc: TDoc) -> None:
        self._ensure_open()
        self.save(family, new_ref, doc)
        old_branch, old_resolved = self._resolved_target(family, old_ref)
        new_branch, _ = self._resolved_target(family, new_ref)
        if old_branch != new_branch:
            raise ValueError(
                f"Transaction branch mismatch for move: expected {new_branch!r}, got {old_branch!r}"
            )
        old_relpath = normalized_path(old_resolved.relpath)
        new_relpath = normalized_path(family.resolve_ref(self.repo, new_ref).relpath)
        if old_relpath != new_relpath:
            self._deletes.add(old_relpath)
            self._adds.pop(old_relpath, None)

    def commit(self) -> str:
        if self._commit_sha is not None:
            return self._commit_sha
        if self.repo.git is None:
            raise ValueError("artifact transactions require a git-backed repository")
        if self.branch is None:
            raise ValueError("artifact transaction has no target branch")
        self._commit_sha = self.repo.git.commit_batch(
            adds=self._adds,
            deletes=sorted(self._deletes),
            message=self.message,
            branch=self.branch,
        )
        return self._commit_sha

    def _resolved_target(
        self,
        family: ArtifactFamily[TRef, object],
        ref: TRef,
    ) -> tuple[str, ResolvedArtifact]:
        resolved = family.resolve_ref(self.repo, ref)
        branch = self.branch or resolved.branch
        if self.branch is None:
            self.branch = branch
        elif branch != self.branch:
            raise ValueError(f"Transaction branch mismatch: expected {self.branch!r}, got {branch!r}")
        return branch, resolved

    def _ensure_open(self) -> None:
        if self._commit_sha is not None:
            raise ValueError("artifact transaction is already committed")


def normalized_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")
