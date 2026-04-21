from __future__ import annotations

import ast
from pathlib import Path


def test_description_kinds_does_not_import_argumentation() -> None:
    path = Path("propstore/core/lemon/description_kinds.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    violations: list[str] = []
    for imported in imports:
        if isinstance(imported, ast.ImportFrom):
            module = imported.module or ""
        else:
            module = imported.names[0].name
        if module.startswith("argumentation"):
            violations.append(f"{path}:{imported.lineno} imports {module}")

    assert violations == []
