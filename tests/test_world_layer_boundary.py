"""Layer boundary enforcement: propstore/world/ must not import from propstore/repo/.

Per CLAUDE.md architectural layers, the world (concept/semantic) layer sits
below the render layer and above pure storage. It must not reach into
propstore.repo, which is the git-backed source-of-truth storage layer.

This test walks every .py file under propstore/world/ and asserts zero
`from propstore.repo...` or `import propstore.repo...` statements.
"""
from __future__ import annotations

import ast
from pathlib import Path


def test_world_package_does_not_import_from_propstore_repo() -> None:
    world_dir = Path("propstore/world")
    assert world_dir.exists(), f"expected world dir at {world_dir.resolve()}"

    offenders: list[tuple[str, int, str]] = []
    for py_file in world_dir.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "propstore.repo" or node.module.startswith(
                    "propstore.repo."
                ):
                    offenders.append((str(py_file), node.lineno, node.module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "propstore.repo" or alias.name.startswith(
                        "propstore.repo."
                    ):
                        offenders.append((str(py_file), node.lineno, alias.name))

    assert offenders == [], (
        f"propstore/world/ imports from propstore/repo/ (layer violation): {offenders}"
    )
