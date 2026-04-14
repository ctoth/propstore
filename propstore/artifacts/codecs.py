from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

import msgspec

from propstore.document_schema import convert_document_value, decode_document_bytes

TDocument = TypeVar("TDocument")


def _prune_none(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            key: _prune_none(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_prune_none(item) for item in value]
    return value


def document_to_payload(document: object) -> object:
    from propstore.core.concepts import ConceptDocument, concept_document_to_payload

    if isinstance(document, ConceptDocument):
        return _prune_none(concept_document_to_payload(document))
    to_payload = getattr(document, "to_payload", None)
    if callable(to_payload):
        return _prune_none(to_payload())
    if isinstance(document, msgspec.Struct):
        return _prune_none(msgspec.to_builtins(document))
    raise TypeError(f"Artifact document {type(document).__name__} is not serializable")


def encode_document(document: object) -> bytes:
    return msgspec.yaml.encode(document_to_payload(document))


def render_document(document: object) -> str:
    return encode_document(document).decode("utf-8").rstrip()


def convert_document(
    payload: object,
    document_type: type[TDocument],
    *,
    source: str,
) -> TDocument:
    return convert_document_value(payload, document_type, source=source)


def decode_document(
    payload: bytes,
    document_type: type[TDocument],
    *,
    source: str,
) -> TDocument:
    return decode_document_bytes(payload, document_type, source=source)
