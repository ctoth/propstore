from __future__ import annotations

import ast
from pathlib import Path


RELATION_KERNEL = Path("propstore/core/relations/kernel.py")

FORBIDDEN_IMPORT_PREFIXES = (
    "propstore.app",
    "propstore.calibrate",
    "propstore.cli",
    "propstore.context_lifting",
    "propstore.grounding",
    "propstore.opinion",
    "propstore.praf",
    "propstore.sidecar",
    "propstore.world",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_relation_kernel_exists_as_shallow_owner_module() -> None:
    assert RELATION_KERNEL.exists()


def test_relation_kernel_does_not_import_downstream_semantic_layers() -> None:
    imports = _imported_modules(RELATION_KERNEL)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()
