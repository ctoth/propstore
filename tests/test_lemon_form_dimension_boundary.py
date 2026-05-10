from __future__ import annotations

import ast
from pathlib import Path

from propstore.core.lemon import LexicalForm


ROOT = Path(__file__).resolve().parents[1]
PROPSTORE = ROOT / "propstore"
DIMENSION_API = {
    "ExtraUnitDefinition",
    "UnitConversion",
    "_PINT_ALIASES",
    "_pint_unit",
    "dims_signature",
    "forms_with_dimensions",
    "from_si",
    "normalize_to_si",
    "required_dimensions",
    "ureg",
    "verify_form_algebra_dimensions",
}


def _production_files() -> list[Path]:
    return sorted(
        path
        for path in PROPSTORE.rglob("*.py")
        if _is_production_file(path)
    )


def _is_production_file(path: Path) -> bool:
    return "__pycache__" not in path.parts and path.name != "_import_linter_negative_fixture.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_dimension_algebra_has_canonical_module() -> None:
    import propstore.dimensions as dimensions

    for name in DIMENSION_API:
        assert hasattr(dimensions, name), name


def test_form_utils_no_longer_owns_dimension_algebra() -> None:
    import propstore.form_utils as form_utils

    path = PROPSTORE / "form_utils.py"
    tree = _parse(path)
    class_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assigned_names = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert "pint" not in imported_modules
    assert DIMENSION_API.isdisjoint(class_names | function_names | assigned_names)
    for name in DIMENSION_API:
        assert not hasattr(form_utils, name), name


def test_production_callers_do_not_import_dimension_api_from_form_utils() -> None:
    offenders: list[tuple[str, str]] = []
    for path in _production_files():
        if path == PROPSTORE / "form_utils.py":
            continue
        for node in ast.walk(_parse(path)):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "propstore.form_utils":
                continue
            for alias in node.names:
                if alias.name in DIMENSION_API:
                    offenders.append((_relative(path), alias.name))

    assert offenders == []


def test_production_file_scan_excludes_import_linter_negative_fixture() -> None:
    fixture = PROPSTORE / "source" / "_import_linter_negative_fixture.py"
    assert not _is_production_file(fixture)


def test_lexical_form_lives_in_lemon_forms_module() -> None:
    assert LexicalForm.__module__ == "propstore.core.lemon.forms"
