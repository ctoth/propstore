"""Typed envelopes for loaded knowledge-tree documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar, cast

from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path

TDocument = TypeVar("TDocument")


@dataclass(init=False)
class LoadedDocument(Generic[TDocument]):
    """A typed YAML document loaded from the semantic knowledge tree."""

    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    document: TDocument

    def __init__(
        self,
        filename: str,
        source_path: KnowledgePath | Path | None = None,
        document: TDocument | None = None,
        knowledge_root: KnowledgePath | Path | None = None,
    ) -> None:
        self.filename = filename
        self.source_path = (
            None if source_path is None else coerce_knowledge_path(source_path)
        )
        self.knowledge_root = (
            None if knowledge_root is None else coerce_knowledge_path(knowledge_root)
        )
        self.document = cast(TDocument, document)
