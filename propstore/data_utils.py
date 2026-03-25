"""Shared data utilities usable by any layer.

This module holds I/O helpers that multiple layers need (heuristic,
CLI, argumentation) without creating layer-violation imports.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def write_yaml_file(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with consistent formatting.

    Uses block style, preserves key order, and writes unicode directly.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
