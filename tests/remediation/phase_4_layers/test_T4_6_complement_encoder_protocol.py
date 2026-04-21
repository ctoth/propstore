from __future__ import annotations

import ast
from pathlib import Path


def test_aspic_grounding_bridge_imports_only_complement_protocol() -> None:
    tree = ast.parse(Path("propstore/aspic_bridge/grounding.py").read_text(encoding="utf-8"))

    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    imported_modules = {
        alias.name
        for node in imports
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in imports
        if isinstance(node, ast.ImportFrom)
    }
    complement_imports = [
        node
        for node in imports
        if isinstance(node, ast.ImportFrom)
        and node.module == "propstore.grounding.complement"
        and any(alias.name == "ComplementEncoder" for alias in node.names)
    ]
    local_functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert complement_imports
    assert "_gunray_complement" not in local_functions
    assert not any(module == "gunray" or module.startswith("gunray.") for module in imported_modules)


def test_gunray_complement_encoder_lives_in_grounding_adapter() -> None:
    from propstore.grounding.gunray_complement import GunrayComplementEncoder

    encoder = GunrayComplementEncoder()
    assert encoder.complement("flies") == "~flies"
    assert encoder.complement("~flies") == "flies"
