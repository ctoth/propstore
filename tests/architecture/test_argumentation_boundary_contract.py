from __future__ import annotations

import ast
from pathlib import Path


ALLOWED_AF_REVISION_IMPORT_OWNER = "propstore.support_revision.argumentation_adapter"


def _module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def _imports_af_revision(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "argumentation.af_revision" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module == "argumentation.af_revision":
            return True
    return False


def test_formal_af_revision_import_edge_is_adapter_only() -> None:
    edges = [
        _module_name(path)
        for path in Path("propstore").rglob("*.py")
        if "__pycache__" not in path.parts and _imports_af_revision(path)
    ]

    assert edges in ([], [ALLOWED_AF_REVISION_IMPORT_OWNER])
