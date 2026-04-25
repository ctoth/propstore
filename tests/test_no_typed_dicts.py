from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPSTORE = ROOT / "propstore"


def _production_files() -> list[Path]:
    return sorted(
        path
        for path in PROPSTORE.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_production_code_does_not_use_typed_dicts() -> None:
    offenders: list[tuple[str, int, str]] = []
    for path in _production_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "TypedDict":
                        offenders.append((_relative(path), node.lineno, "import TypedDict"))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "typing":
                        offenders.append((_relative(path), node.lineno, "import typing"))
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "TypedDict":
                        offenders.append((_relative(path), node.lineno, f"class {node.name}(TypedDict)"))
                    elif isinstance(base, ast.Attribute) and base.attr == "TypedDict":
                        offenders.append((_relative(path), node.lineno, f"class {node.name}(typing.TypedDict)"))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "TypedDict":
                    offenders.append((_relative(path), node.lineno, "TypedDict(...)"))
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "TypedDict":
                    offenders.append((_relative(path), node.lineno, "typing.TypedDict(...)"))

    assert offenders == []
