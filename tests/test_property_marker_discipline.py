from __future__ import annotations

import ast
from pathlib import Path


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ""


def test_every_hypothesis_given_test_is_marked_property() -> None:
    missing: list[str] = []
    for path in sorted(Path("tests").glob("test_*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = {_decorator_name(decorator) for decorator in node.decorator_list}
            if not any(name == "given" or name.endswith(".given") for name in decorators):
                continue
            if "pytest.mark.property" not in decorators:
                missing.append(f"{path}:{node.lineno}:{node.name}")

    assert missing == []
