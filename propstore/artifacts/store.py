from __future__ import annotations

from typing import TYPE_CHECKING

from quire.family_store import DocumentFamilyStore

from propstore.artifacts.codecs import (
    convert_document,
    decode_document,
    document_to_payload,
    encode_document,
    render_document,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


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


def _convert_document(payload: object, document_type: type[object], source: str) -> object:
    return convert_document(payload, document_type, source=source)


def _decode_document(payload: bytes, document_type: type[object], source: str) -> object:
    return decode_document(payload, document_type, source=source)
