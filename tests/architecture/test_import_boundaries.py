from __future__ import annotations

import ast
from pathlib import Path


RELATION_KERNEL = Path("propstore/core/relations/kernel.py")
ASSERTION_REFS = Path("propstore/core/assertions/refs.py")
ASSERTION_SITUATED = Path("propstore/core/assertions/situated.py")
ASSERTION_CONVERSION = Path("propstore/core/assertions/conversion.py")
ASSERTION_CODEC = Path("propstore/core/assertions/codec.py")
CONDITION_IR = Path("propstore/core/conditions/ir.py")
CONDITION_CHECKED = Path("propstore/core/conditions/checked.py")
CONDITION_CEL_FRONTEND = Path("propstore/core/conditions/cel_frontend.py")
CONDITION_PYTHON_BACKEND = Path("propstore/core/conditions/python_backend.py")
CONDITION_ESTREE_BACKEND = Path("propstore/core/conditions/estree_backend.py")
CONDITION_Z3_BACKEND = Path("propstore/core/conditions/z3_backend.py")

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
FORBIDDEN_CONDITION_IR_IMPORT_PREFIXES = FORBIDDEN_IMPORT_PREFIXES + (
    "ast",
    "propstore.cel_checker",
)
FORBIDDEN_CONDITION_FRONTEND_IMPORT_PREFIXES = tuple(
    prefix
    for prefix in FORBIDDEN_IMPORT_PREFIXES
    if prefix != "propstore.cel_checker"
) + ("ast",)
FORBIDDEN_CONDITION_BACKEND_IMPORT_PREFIXES = FORBIDDEN_IMPORT_PREFIXES + (
    "propstore.cel_checker",
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


def test_assertion_codec_exists_as_shallow_owner_module() -> None:
    assert ASSERTION_CODEC.exists()


def test_assertion_codec_does_not_import_downstream_semantic_layers() -> None:
    imports = _imported_modules(ASSERTION_CODEC)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_ir_exists_as_shallow_owner_module() -> None:
    assert CONDITION_IR.exists()


def test_condition_ir_does_not_import_frontend_or_backend_layers() -> None:
    imports = _imported_modules(CONDITION_IR)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_IR_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_checked_exists_as_shallow_owner_module() -> None:
    assert CONDITION_CHECKED.exists()


def test_condition_checked_does_not_import_frontend_or_backend_layers() -> None:
    imports = _imported_modules(CONDITION_CHECKED)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_IR_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_cel_frontend_exists_as_shallow_adapter_module() -> None:
    assert CONDITION_CEL_FRONTEND.exists()


def test_condition_cel_frontend_does_not_import_backend_layers() -> None:
    imports = _imported_modules(CONDITION_CEL_FRONTEND)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_FRONTEND_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_python_backend_exists_as_backend_module() -> None:
    assert CONDITION_PYTHON_BACKEND.exists()


def test_condition_python_backend_does_not_import_frontend_or_other_backends() -> None:
    imports = _imported_modules(CONDITION_PYTHON_BACKEND)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_BACKEND_IMPORT_PREFIXES
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_estree_backend_exists_as_backend_module() -> None:
    assert CONDITION_ESTREE_BACKEND.exists()


def test_condition_estree_backend_does_not_import_frontend_or_other_backends() -> None:
    imports = _imported_modules(CONDITION_ESTREE_BACKEND)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_BACKEND_IMPORT_PREFIXES + ("ast",)
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()


def test_condition_z3_backend_exists_as_backend_module() -> None:
    assert CONDITION_Z3_BACKEND.exists()


def test_condition_z3_backend_does_not_import_frontend_or_other_backends() -> None:
    imports = _imported_modules(CONDITION_Z3_BACKEND)

    forbidden = {
        imported
        for imported in imports
        for prefix in FORBIDDEN_CONDITION_BACKEND_IMPORT_PREFIXES
        + ("ast", "propstore.core.conditions.estree_backend")
        if imported == prefix or imported.startswith(f"{prefix}.")
    }

    assert forbidden == set()
