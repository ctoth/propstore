from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from quire.family_store import DocumentFamilyStore
from quire.tree_path import GitTreePath

from propstore.artifacts.codecs import (
    convert_document,
    decode_document,
    document_to_payload,
    encode_document,
    render_document,
)

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository


@dataclass(frozen=True)
class _GitArtifactOwner:
    git: GitStore

    def tree(self, commit: str | None = None) -> GitTreePath:
        return GitTreePath(self.git, commit=commit)


def create_artifact_store(repo: Repository) -> DocumentFamilyStore[Repository]:
    return DocumentFamilyStore(
        owner=repo,
        backend=repo.git,
        convert_document=_convert_document,
        decode_document=_decode_document,
        encode_document=encode_document,
        render_document_value=render_document,
        document_to_payload=document_to_payload,
    )


def create_artifact_store_for_git(git: GitStore) -> DocumentFamilyStore[Repository]:
    owner = cast("Repository", _GitArtifactOwner(git=git))
    return DocumentFamilyStore(
        owner=owner,
        backend=git,
        convert_document=_convert_document,
        decode_document=_decode_document,
        encode_document=encode_document,
        render_document_value=render_document,
        document_to_payload=document_to_payload,
    )


def _convert_document(payload: object, document_type: type[object], source: str) -> object:
    return convert_document(payload, document_type, source=source)


def _decode_document(payload: bytes, document_type: type[object], source: str) -> object:
    return decode_document(payload, document_type, source=source)
