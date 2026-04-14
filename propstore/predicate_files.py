"""Loaded-predicate file helpers for the grounding pipeline."""

from __future__ import annotations

from propstore.artifacts.documents.predicates import (
    PredicateDocument,
    PredicatesFileDocument,
)
from propstore.loaded import LoadedDocument


class LoadedPredicateFile(LoadedDocument[PredicatesFileDocument]):
    """Typed predicates-file envelope."""

    @classmethod
    def from_loaded_document(
        cls,
        document: LoadedDocument[PredicatesFileDocument],
    ) -> LoadedPredicateFile:
        return cls(
            filename=document.filename,
            source_path=document.source_path,
            knowledge_root=document.knowledge_root,
            document=document.document,
        )

    @property
    def predicates(self) -> tuple[PredicateDocument, ...]:
        return self.document.predicates
