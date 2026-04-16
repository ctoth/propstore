"""Shared schema-bound YAML document decoding."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from pathlib import Path
from typing import Generic, TypeVar, overload

import msgspec

from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.loaded import LoadedDocument

TDocument = TypeVar("TDocument")
TLoaded = TypeVar("TLoaded")


class DocumentStruct(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Base type for authored YAML document schemas."""


class DocumentSchemaError(ValueError):
    """Raised when a document fails strict schema decoding."""

    def __init__(self, source: str, message: str) -> None:
        super().__init__(f"{source}: {message}")
        self.source = source
        self.message = message


def to_document_builtins(value: object) -> object:
    if isinstance(value, msgspec.Struct):
        return to_document_builtins(msgspec.to_builtins(value))
    if isinstance(value, Mapping):
        return {
            key: to_document_builtins(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [to_document_builtins(item) for item in value]
    if isinstance(value, list):
        return [to_document_builtins(item) for item in value]
    return value


def _source_label(path: KnowledgePath | Path) -> str:
    if isinstance(path, Path):
        return str(path)
    rendered = path.as_posix()
    return rendered if rendered else path.cache_key()


def decode_document_bytes(
    payload: bytes,
    document_type: type[TDocument],
    *,
    source: str,
) -> TDocument:
    """Decode YAML bytes into a strict typed document."""

    try:
        return msgspec.yaml.decode(payload, type=document_type, strict=True)
    except msgspec.DecodeError as exc:
        raise DocumentSchemaError(source, str(exc)) from exc


def convert_document_value(
    payload: object,
    document_type: type[TDocument],
    *,
    source: str,
) -> TDocument:
    """Validate already-loaded Python data against a strict document schema."""

    try:
        return msgspec.convert(payload, type=document_type, strict=True)
    except (msgspec.ValidationError, TypeError) as exc:
        raise DocumentSchemaError(source, str(exc)) from exc


def decode_document_path(
    path: KnowledgePath | Path,
    document_type: type[TDocument],
) -> TDocument:
    """Read and decode a typed YAML document from a filesystem or knowledge path."""

    knowledge_path = coerce_knowledge_path(path)
    return decode_document_bytes(
        knowledge_path.read_bytes(),
        document_type,
        source=_source_label(knowledge_path),
    )


def load_document(
    path: KnowledgePath | Path,
    document_type: type[TDocument],
    *,
    knowledge_root: KnowledgePath | Path | None = None,
) -> LoadedDocument[TDocument]:
    """Load a typed document together with its source metadata."""

    source_path = coerce_knowledge_path(path)
    root_path = None if knowledge_root is None else coerce_knowledge_path(knowledge_root)
    return LoadedDocument(
        filename=source_path.stem,
        source_path=source_path,
        knowledge_root=root_path,
        document=decode_document_path(source_path, document_type),
    )


@overload
def load_document_dir(
    directory: KnowledgePath | Path | None,
    document_type: type[TDocument],
) -> list[LoadedDocument[TDocument]]: ...


@overload
def load_document_dir(
    directory: KnowledgePath | Path | None,
    document_type: type[TDocument],
    *,
    wrapper: Callable[[LoadedDocument[TDocument]], TLoaded],
) -> list[TLoaded]: ...


def load_document_dir(
    directory: KnowledgePath | Path | None,
    document_type: type[TDocument],
    *,
    wrapper: Callable[[LoadedDocument[TDocument]], TLoaded] | None = None,
) -> list[LoadedDocument[TDocument]] | list[TLoaded]:
    """Load direct child YAML documents from a concrete knowledge-tree directory."""

    if directory is None:
        return []

    documents_dir = coerce_knowledge_path(directory)
    if not documents_dir.is_dir():
        return []

    knowledge_root = documents_dir.parent if documents_dir.name else documents_dir
    entries = sorted(
        (
            entry
            for entry in documents_dir.iterdir()
            if entry.is_file() and entry.suffix == ".yaml"
        ),
        key=lambda entry: entry.as_posix(),
    )
    loaded = [
        load_document(
            entry,
            document_type,
            knowledge_root=knowledge_root,
        )
        for entry in entries
    ]

    if wrapper is None:
        return loaded
    return [wrapper(document) for document in loaded]
