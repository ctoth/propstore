"""Shared serialization utilities usable by any layer."""
from __future__ import annotations

from pathlib import Path

import msgspec
import yaml


def load_yaml_dir(directory: Path) -> list[tuple[str, Path, dict]]:
    """Load all .yaml files from a directory, sorted by filename.

    Returns a list of (stem, filepath, data) tuples.
    Empty YAML files produce an empty dict.
    """
    results: list[tuple[str, Path, dict]] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            raw = entry.read_bytes()
            if raw.strip():
                decoded = msgspec.yaml.decode(raw)
                if not isinstance(decoded, dict):
                    raise ValueError(f"{entry}: expected a YAML mapping")
                data = decoded
            else:
                data = {}
            results.append((entry.stem, entry, data if data else {}))
    return results


def write_yaml_file(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with consistent formatting.

    Uses block style, preserves key order, and writes unicode directly.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
