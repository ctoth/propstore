"""Shared data utilities usable by any layer.

This module holds I/O helpers that multiple layers need (heuristic,
CLI, argumentation) without creating layer-violation imports.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


def write_yaml_file(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with consistent formatting.

    Uses block style, preserves key order, and writes unicode directly.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_concept_file(path: Path) -> dict:
    """Load a single concept YAML file and return its data as a dict."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


_ID_RE = re.compile(r'^concept\d+$')


def find_concept(id_or_name: str, cdir: Path) -> Path | None:
    """Find a concept file by ID or canonical_name. Returns filepath or None."""
    if not cdir.exists():
        return None

    # Try as canonical_name (direct file lookup)
    direct = cdir / f"{id_or_name}.yaml"
    if direct.exists():
        return direct

    # Try as ID — scan files
    if _ID_RE.match(id_or_name):
        for entry in sorted(cdir.iterdir()):
            if entry.is_file() and entry.suffix == ".yaml":
                data = load_concept_file(entry)
                if data.get("id") == id_or_name:
                    return entry
    return None


def load_all_concepts_by_id(cdir: Path) -> dict[str, dict]:
    """Load all concepts keyed by ID."""
    if not cdir.exists():
        return {}
    result: dict[str, dict] = {}
    for entry in sorted(cdir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            data = load_concept_file(entry)
            cid = data.get("id")
            if cid:
                result[cid] = data
    return result
