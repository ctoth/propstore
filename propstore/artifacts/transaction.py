from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.artifacts.codecs import encode_document
from propstore.artifacts.types import ArtifactFamily, ArtifactContext, TDoc, TRef

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


@dataclass
class ArtifactTransaction:
    repo: Repository
    message: str
    branch: str | None = None
    _adds: dict[str, bytes] = field(default_factory=dict)
    _deletes: set[str] = field(default_factory=set)

    def save(self, family: ArtifactFamily[TRef, TDoc], ref: TRef, doc: TDoc) -> None:
        resolved = family.resolve_ref(self.repo, ref)
        branch = self.branch or resolved.branch
        if self.branch is None:
            self.branch = branch
        elif branch != self.branch:
            raise ValueError(f"Transaction branch mismatch: expected {self.branch!r}, got {branch!r}")
        context = ArtifactContext(
            repo=self.repo,
            ref=ref,
            branch=branch,
            relpath=resolved.relpath,
        )
        normalized = doc
        if family.normalize_for_write is not None:
            normalized = family.normalize_for_write(context, normalized, self)
        if family.validate_for_write is not None:
            family.validate_for_write(context, normalized, self)
        relpath = normalized_path(resolved.relpath)
        self._adds[relpath] = encode_document(normalized)
        self._deletes.discard(relpath)

    def delete(self, family: ArtifactFamily[TRef, object], ref: TRef) -> None:
        resolved = family.resolve_ref(self.repo, ref)
        branch = self.branch or resolved.branch
        if self.branch is None:
            self.branch = branch
        elif branch != self.branch:
            raise ValueError(f"Transaction branch mismatch: expected {self.branch!r}, got {branch!r}")
        relpath = normalized_path(resolved.relpath)
        self._deletes.add(relpath)
        self._adds.pop(relpath, None)

    def commit(self) -> str:
        if self.repo.git is None:
            raise ValueError("artifact transactions require a git-backed repository")
        if self.branch is None:
            raise ValueError("artifact transaction has no target branch")
        return self.repo.git.commit_batch(
            adds=self._adds,
            deletes=sorted(self._deletes),
            message=self.message,
            branch=self.branch,
        )


def normalized_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")
