"""Unified type for loaded YAML entries from the knowledge tree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path


@dataclass(init=False)
class LoadedEntry:
    """A YAML file loaded from the semantic knowledge tree.

    `source_path` is the canonical location for a loaded artifact. It may be a
    filesystem-backed knowledge path, a git-backed knowledge path, or `None`
    for synthetic/generated entries that do not originate from a source file.
    """

    filename: str
    source_path: KnowledgePath | None
    data: dict[str, Any]

    def __init__(
        self,
        filename: str,
        source_path: KnowledgePath | Path | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.filename = filename
        self.source_path = (
            None if source_path is None else coerce_knowledge_path(source_path)
        )
        self.data = {} if data is None else data
