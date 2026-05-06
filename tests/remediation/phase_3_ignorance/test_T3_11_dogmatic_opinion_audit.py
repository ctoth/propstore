from __future__ import annotations

import ast
from pathlib import Path


def _is_opinion_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id == "Opinion"
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == "Opinion"
    return False


def _is_zero_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and node.value == 0


def _dogmatic_uncertainty_argument(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg == "u":
            return _is_zero_literal(keyword.value)
    return len(node.args) >= 3 and _is_zero_literal(node.args[2])


def _has_explicit_dogmatic_allowance(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg == "allow_dogmatic":
            return isinstance(keyword.value, ast.Constant) and keyword.value.value is True
    return False


def _allowance_line_has_tautology_citation(
    node: ast.Call,
    source_lines: list[str],
) -> bool:
    for keyword in node.keywords:
        if keyword.arg != "allow_dogmatic":
            continue
        line_number = getattr(keyword, "lineno", node.lineno)
        line = source_lines[line_number - 1].lower()
        return "#" in line and "tautology" in line and "josang 2001" in line
    return False


def test_dogmatic_opinion_constructors_are_explicitly_cited() -> None:
    violations: list[str] = []
    for path in sorted(Path("propstore").rglob("*.py")):
        if path.name.startswith("_ws_n2_violation_"):
            continue
        source = path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_opinion_call(node) or not _dogmatic_uncertainty_argument(node):
                continue
            if not _has_explicit_dogmatic_allowance(node):
                violations.append(f"{path}:{node.lineno} missing allow_dogmatic=True")
                continue
            if not _allowance_line_has_tautology_citation(node, source_lines):
                violations.append(f"{path}:{node.lineno} missing same-line Josang 2001 tautology citation")

    assert violations == []
