from __future__ import annotations

import ast
from pathlib import Path


RELATION_KERNEL = Path("propstore/core/relations/kernel.py")
ASSERTION_REFS = Path("propstore/core/assertions/refs.py")
ASSERTION_SITUATED = Path("propstore/core/assertions/situated.py")
ASSERTION_CONVERSION = Path("propstore/core/assertions/conversion.py")

FORBIDDEN_IMPORT_PREFIXES = (
    "propstore.app",
    "propstore.calibrate",
    "propstore.cli",
    "propstore.condition_classifier",
    "propstore.context_lifting",
    "propstore.grounding",
    "propstore.opinion",
    "propstore.praf",
    "propstore.sidecar",
    "propstore.world",
    "propstore.z3_conditions",
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


def test_assertion_refs_exist_as_shallow_owner_module() -> None:
    assert ASSERTION_REFS.exists()


def test_assertion_refs_do_not_import_downstream_semantic_layers() -> None:
    imports = _imported_modules(ASSERTION_REFS)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_situated_assertions_exist_as_shallow_owner_module() -> None:
    assert ASSERTION_SITUATED.exists()


def test_situated_assertions_do_not_import_downstream_semantic_layers() -> None:
    imports = _imported_modules(ASSERTION_SITUATED)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_assertion_conversion_exists_as_shallow_owner_module() -> None:
    assert ASSERTION_CONVERSION.exists()


def test_assertion_conversion_does_not_import_downstream_semantic_layers() -> None:
    imports = _imported_modules(ASSERTION_CONVERSION)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()
