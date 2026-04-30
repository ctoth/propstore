from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


def test_world_query_is_the_public_query_surface() -> None:
    propstore = importlib.import_module("propstore")

    assert propstore.WorldQuery.__name__ == "WorldQuery"
    assert propstore.WorldQuery.__module__ == "propstore.world.model"
    with pytest.raises(ImportError):
        exec("from propstore import WorldModel", {})


def test_world_model_identifier_is_absent_from_propstore_and_tests() -> None:
    offenders: list[str] = []
    for root in (Path("propstore"), Path("tests")):
        for path in root.rglob("*.py"):
            if path == Path(__file__):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == "WorldModel":
                    offenders.append(f"{path}:{node.lineno}")
                if isinstance(node, ast.Attribute) and node.attr == "WorldModel":
                    offenders.append(f"{path}:{node.lineno}")

    assert offenders == []
