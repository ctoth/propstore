from __future__ import annotations

import ast
from pathlib import Path


PRODUCTION_ROOT = Path("propstore")
CONDITION_FRONTEND = Path("propstore/core/conditions/cel_frontend.py")
CONDITION_CHECKED = Path("propstore/core/conditions/checked.py")
CONDITION_Z3_IMPORTERS = {
    Path("propstore/core/conditions/solver.py"),
    Path("propstore/core/conditions/z3_backend.py"),
}


def _production_python_files() -> tuple[Path, ...]:
    return tuple(
        path
        for path in sorted(PRODUCTION_ROOT.rglob("*.py"))
        if path.exists()
    )


def _imports(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set()
    tree = ast.parse(text)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_no_production_imports_deleted_z3_conditions_surface() -> None:
    offenders = {
        str(path): sorted(
            imported
            for imported in _imports(path)
            if imported == "propstore.z3_conditions"
            or imported.startswith("propstore.z3_conditions.")
        )
        for path in _production_python_files()
    }
    offenders = {path: imports for path, imports in offenders.items() if imports}

    assert offenders == {}


def test_raw_z3_import_is_confined_to_condition_solver_boundary() -> None:
    offenders = {
        str(path): sorted(
            imported
            for imported in _imports(path)
            if imported == "z3" or imported.startswith("z3.")
        )
        for path in _production_python_files()
        if path not in CONDITION_Z3_IMPORTERS
    }
    offenders = {path: imports for path, imports in offenders.items() if imports}

    assert offenders == {}


def test_cel_parser_import_is_confined_to_condition_frontend_boundary() -> None:
    allowed = {CONDITION_FRONTEND}
    offenders = {
        str(path): sorted(
            imported
            for imported in _imports(path)
            if imported == "cel_parser" or imported.startswith("cel_parser.")
        )
        for path in _production_python_files()
        if path not in allowed
    }
    offenders = {path: imports for path, imports in offenders.items() if imports}

    assert offenders == {}


def test_checked_condition_carrier_names_no_frontend_ast_or_backend_surfaces() -> None:
    tree = ast.parse(CONDITION_CHECKED.read_text(encoding="utf-8"))
    observed: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            observed.add(node.arg)
        elif isinstance(node, ast.Attribute):
            observed.add(node.attr)
        elif isinstance(node, ast.Name):
            observed.add(node.id)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            observed.add(node.name)

    assert observed.isdisjoint(
        {
            "ast",
            "cel_ast",
            "raw_cel_ast",
            "Z3",
            "Solver",
            "RuntimeHelper",
            "PythonAst",
        }
    )


def test_by_final_cutover_only_cel_frontend_imports_cel_parser() -> None:
    offenders = {
        str(path): sorted(
            imported
            for imported in _imports(path)
            if imported == "cel_parser" or imported.startswith("cel_parser.")
        )
        for path in _production_python_files()
        if path != CONDITION_FRONTEND
    }
    offenders = {path: imports for path, imports in offenders.items() if imports}

    assert offenders == {}
