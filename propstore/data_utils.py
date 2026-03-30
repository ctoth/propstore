"""Shared data utilities usable by any layer.

This module holds I/O helpers that multiple layers need (heuristic,
CLI, argumentation) without creating layer-violation imports.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path


def write_yaml_file(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with consistent formatting.

    Uses block style, preserves key order, and writes unicode directly.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_concept_file(path: KnowledgePath | Path) -> dict:
    """Load a single concept YAML file and return its data as a dict."""
    data = yaml.safe_load(coerce_knowledge_path(path).read_bytes())
    return data if data else {}


_ID_RE = re.compile(r'^concept\d+$')


def find_concept(id_or_name: str, cdir: KnowledgePath | Path) -> KnowledgePath | None:
    """Find a concept file by ID or canonical_name."""
    concepts_dir = coerce_knowledge_path(cdir)
    if not concepts_dir.exists():
        return None

    # Try as canonical_name (direct file lookup)
    direct = concepts_dir / f"{id_or_name}.yaml"
    if direct.exists():
        return direct

    # Try as ID — scan files
    if _ID_RE.match(id_or_name):
        for entry in concepts_dir.iterdir():
            if entry.is_file() and entry.suffix == ".yaml":
                data = load_concept_file(entry)
                if data.get("id") == id_or_name:
                    return entry
    return None


def load_all_concepts_by_id(cdir: KnowledgePath | Path) -> dict[str, dict]:
    """Load all concepts keyed by ID."""
    concepts_dir = coerce_knowledge_path(cdir)
    if not concepts_dir.exists():
        return {}
    result: dict[str, dict] = {}
    for entry in concepts_dir.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            data = load_concept_file(entry)
            cid = data.get("id")
            if cid:
                result[cid] = data
    return result
