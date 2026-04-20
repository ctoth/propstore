"""Context family document, stage, and pass ownership."""

from __future__ import annotations

from quire.documents import load_document_dir

from propstore.families.contexts.documents import ContextDocument

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quire.tree_path import TreePath as KnowledgePath
    from propstore.families.contexts.stages import LoadedContext


def load_contexts(contexts_dir: KnowledgePath | None) -> list[LoadedContext]:
    from propstore.families.contexts.stages import LoadedContext

    return load_document_dir(
        contexts_dir,
        ContextDocument,
        wrapper=LoadedContext.from_loaded_document,
    )


__all__ = [
    "ContextDocument",
    "load_contexts",
]
