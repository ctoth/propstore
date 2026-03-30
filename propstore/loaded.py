"""Unified type for loaded YAML entries from the knowledge tree."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoadedEntry:
    """A YAML file loaded from a knowledge tree subdirectory.

    Every entity in the knowledge tree (concept, claim, context, stance)
    shares this shape: a filename stem, an optional filesystem path, and
    parsed YAML data.
    """
    filename: str        # stem, no extension
    filepath: Path | None
    data: dict
