"""Executable boundary contract for the support-revision package."""

from __future__ import annotations

import ast
from pathlib import Path


_PACKAGE_INIT = Path("propstore/support_revision/__init__.py")


def test_support_revision_package_import_is_shallow() -> None:
    tree = ast.parse(_PACKAGE_INIT.read_text(encoding="utf-8"))

    eager_imports = [
        node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assigned_names = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        if isinstance(target, ast.Name)
    }

    assert eager_imports == []
    assert "__all__" not in assigned_names


def test_dispatch_submodule_resolves_without_package_facade() -> None:
    from propstore.support_revision import dispatch

    assert dispatch.__name__ == "propstore.support_revision.dispatch"
