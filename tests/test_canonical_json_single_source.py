from __future__ import annotations

import ast
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
import pytest

from quire import canonical_json_bytes


def test_propstore_defines_no_local_canonical_json_helpers() -> None:
    offenders: list[str] = []
    for path in Path("propstore").rglob("*.py"):
        if path.name.startswith("_ws_n2_violation_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_canonical_json":
                offenders.append(f"{path}:{node.lineno}")

    assert offenders == []
