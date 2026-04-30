from __future__ import annotations

import ast
from pathlib import Path


EXCLUDED_PARTS = {"cli", "web"}


def _production_paths() -> tuple[Path, ...]:
    return tuple(
        path
        for path in Path("propstore").rglob("*.py")
        if not (set(path.parts) & EXCLUDED_PARTS)
    )


def test_owner_modules_do_not_own_process_streams_or_argv_parsing() -> None:
    offenders: list[str] = []
    for path in _production_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"argparse", "click"}:
                        offenders.append(f"{path}:{node.lineno}:import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in {"argparse", "click"}:
                    offenders.append(f"{path}:{node.lineno}:from {node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    for keyword in node.keywords:
                        if (
                            keyword.arg == "file"
                            and isinstance(keyword.value, ast.Attribute)
                            and keyword.value.attr == "stderr"
                        ):
                            offenders.append(f"{path}:{node.lineno}:print stderr")
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "exit"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "sys"
                ):
                    offenders.append(f"{path}:{node.lineno}:sys.exit")

    assert offenders == []
