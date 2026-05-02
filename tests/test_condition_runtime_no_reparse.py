from __future__ import annotations

import ast
from pathlib import Path


RUNTIME_MODULES = (
    Path("propstore/core/activation.py"),
    Path("propstore/condition_classifier.py"),
    Path("propstore/context_lifting.py"),
    Path("propstore/world/model.py"),
    Path("propstore/world/bound.py"),
    Path("propstore/world/assignment_selection_merge.py"),
    Path("propstore/conflict_detector/orchestrator.py"),
    Path("propstore/conflict_detector/parameter_claims.py"),
)


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imports(path: Path) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _names(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def test_runtime_condition_paths_do_not_import_cel_parser_or_old_solver() -> None:
    offenders: dict[str, list[str]] = {}
    for path in RUNTIME_MODULES:
        imports = _imports(path)
        bad = sorted(
            imported
            for imported in imports
            if imported == "cel_parser"
            or imported.startswith("cel_parser.")
            or imported == "propstore.z3_conditions"
            or imported.startswith("propstore.z3_conditions.")
        )
        if bad:
            offenders[str(path)] = bad

    assert offenders == {}


def test_runtime_condition_paths_do_not_reparse_conditions_cel_json() -> None:
    offenders: dict[str, list[str]] = {}
    forbidden_names = {
        "_claim_conditions",
        "_cel_identifier_names",
        "_synthetic_names_from_conditions",
        "parse_cel",
    }
    for path in RUNTIME_MODULES:
        observed = _names(path)
        bad = sorted(observed & forbidden_names)
        if bad:
            offenders[str(path)] = bad

    assert offenders == {}


def test_runtime_condition_paths_use_checked_condition_surface() -> None:
    expected_import = "propstore.core.conditions"
    missing = [
        str(path)
        for path in RUNTIME_MODULES
        if not any(
            imported == expected_import or imported.startswith(f"{expected_import}.")
            for imported in _imports(path)
        )
    ]

    assert missing == []
