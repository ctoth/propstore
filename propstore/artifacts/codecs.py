from __future__ import annotations

from typing import Any, TypeVar

import msgspec

from propstore.document_schema import decode_document_bytes

TDocument = TypeVar("TDocument")


def document_to_payload(document: object) -> object:
    to_payload = getattr(document, "to_payload", None)
    if callable(to_payload):
        return to_payload()
    if isinstance(document, msgspec.Struct):
        return msgspec.to_builtins(document)
    raise TypeError(f"Artifact document {type(document).__name__} is not serializable")


def encode_document(document: object) -> bytes:
    return msgspec.yaml.encode(document_to_payload(document))


def decode_document(
    payload: bytes,
    document_type: type[TDocument],
    *,
    source: str,
) -> TDocument:
    return decode_document_bytes(payload, document_type, source=source)
