"""WS-J Step 7: graph overlays use the honest OverlayWorld name."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


_OLD = "Hypothetical" + "World"
_NEW = "Overlay" + "World"
_DISCLAIMER = "overlay semantics — not a Pearl intervention"


def test_ws_j_old_overlay_name_is_absent_from_python_surfaces() -> None:
    roots = (Path("propstore"), Path("tests"))
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == _OLD:
                    offenders.append(f"{path}:class")
                elif isinstance(node, ast.ImportFrom):
                    offenders.extend(f"{path}:import" for alias in node.names if alias.name == _OLD)
                elif isinstance(node, ast.Import):
                    offenders.extend(f"{path}:import" for alias in node.names if alias.name.endswith(_OLD))
                elif isinstance(node, ast.Name) and node.id == _OLD:
                    offenders.append(f"{path}:name")
                elif isinstance(node, ast.Attribute) and node.attr == _OLD:
                    offenders.append(f"{path}:attr")

    assert offenders == []


def test_ws_j_overlay_world_export_and_docstring_are_explicit() -> None:
    import propstore
    from propstore.world.overlay import OverlayWorld

    with pytest.raises(AttributeError):
        getattr(propstore, _OLD)
    assert getattr(propstore, _NEW) is OverlayWorld
    assert _DISCLAIMER in (OverlayWorld.__doc__ or "")
