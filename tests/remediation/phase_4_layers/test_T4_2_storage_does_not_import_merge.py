from __future__ import annotations

import ast
from pathlib import Path


def test_storage_does_not_import_merge() -> None:
    path = Path("propstore/storage/merge_commit.py")
    if not path.exists():
        return

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "propstore.merge" or module.startswith("propstore.merge."):
                violations.append(f"{path}:{node.lineno} imports {module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                if module == "propstore.merge" or module.startswith("propstore.merge."):
                    violations.append(f"{path}:{node.lineno} imports {module}")

    assert violations == []
