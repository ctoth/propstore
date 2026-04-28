from __future__ import annotations

import ast
import importlib
from pathlib import Path

import quire


def test_propstore_quire_imports_are_public() -> None:
    root_public = set(quire.__all__)
    violations: list[str] = []
    package_root = Path(__file__).resolve().parents[1] / "propstore"

    for source_path in package_root.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module is None or not node.module.startswith("quire"):
                continue
            module = importlib.import_module(node.module)
            module_public = set(getattr(module, "__all__", ()))
            for alias in node.names:
                if alias.name == "*":
                    continue
                if alias.name not in root_public and alias.name not in module_public:
                    rel = source_path.relative_to(package_root.parent).as_posix()
                    violations.append(f"{rel}: from {node.module} import {alias.name}")

    assert violations == []
