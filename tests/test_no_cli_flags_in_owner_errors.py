from __future__ import annotations

import ast
import re
from pathlib import Path


OWNER_ROOTS = (
    Path("propstore/app"),
    Path("propstore/source"),
    Path("propstore/world"),
    Path("propstore/sidecar"),
    Path("propstore/heuristic"),
    Path("propstore/storage"),
)

FLAG_RE = re.compile(r"--[A-Za-z][A-Za-z0-9_-]*")


def _string_constants(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def test_owner_layer_exceptions_do_not_name_cli_flags() -> None:
    offenders: list[str] = []
    for root in OWNER_ROOTS:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise):
                    for value in _string_constants(node):
                        if FLAG_RE.search(value):
                            offenders.append(f"{path}:{node.lineno}:{value}")

    assert offenders == []
