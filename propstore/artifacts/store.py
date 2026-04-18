from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from quire.family_store import DocumentFamilyStore

from propstore.artifacts.codecs import (
    convert_document,
    decode_document,
    document_to_payload,
    encode_document,
    render_document,
)
from propstore.storage.branch import branch_head

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.storage import GitStore


class ArtifactRepository(DocumentFamilyStore["Repository"]):
    @classmethod
    def for_git(cls, git: object) -> ArtifactRepository:
        return cls(cast("Repository", SimpleNamespace(git=git)))

    def __init__(self, repo: Repository) -> None:
        super().__init__(
            owner=repo,
            backend=repo.git,
            branch_head=_branch_head,
            convert_document=_convert_document,
            decode_document=_decode_document,
            encode_document=encode_document,
            render_document_value=render_document,
            document_to_payload=document_to_payload,
        )

    @property
    def repo(self) -> Repository:
        return self.owner


def _branch_head(backend: object, branch: str) -> str | None:
    return branch_head(cast("GitStore", backend), branch)


def _convert_document(payload: object, document_type: type[object], source: str) -> object:
    return convert_document(payload, document_type, source=source)


def _decode_document(payload: bytes, document_type: type[object], source: str) -> object:
    return decode_document(payload, document_type, source=source)
