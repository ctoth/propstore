from __future__ import annotations

import ast
from pathlib import Path


def test_revision_modules_do_not_import_ic_merge() -> None:
    revision_dir = Path("propstore/support_revision")
    assert revision_dir.exists()

    for path in sorted(revision_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imports.append(node.module)
        assert "propstore.storage.ic_merge" not in imports
