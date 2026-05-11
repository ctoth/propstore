from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


_TRANSIENT_IMPORT_LINTER_FIXTURE_PREFIXES = (
    "_ws_n2_violation_",
    "_import_linter_negative_fixture",
)


def _is_transient_import_linter_fixture(path: Path) -> bool:
    return path.name.startswith(_TRANSIENT_IMPORT_LINTER_FIXTURE_PREFIXES)


def _world_model_identifier_offenders(roots: tuple[Path, ...]) -> list[str]:
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            if path == Path(__file__) or _is_transient_import_linter_fixture(path):
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                if _is_transient_import_linter_fixture(path):
                    continue
                raise
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == "WorldModel":
                    offenders.append(f"{path}:{node.lineno}")
                if isinstance(node, ast.Attribute) and node.attr == "WorldModel":
                    offenders.append(f"{path}:{node.lineno}")
    return offenders


def test_world_query_is_the_public_query_surface() -> None:
    propstore = importlib.import_module("propstore")

    assert propstore.WorldQuery.__name__ == "WorldQuery"
    assert propstore.WorldQuery.__module__ == "propstore.world.model"
    with pytest.raises(ImportError):
        exec("from propstore import WorldModel", {})


def test_world_model_identifier_is_absent_from_propstore_and_tests() -> None:
    assert _world_model_identifier_offenders((Path("propstore"), Path("tests"))) == []


def test_world_model_identifier_scan_ignores_import_linter_transient_fixture(
    tmp_path: Path,
) -> None:
    root = tmp_path / "propstore"
    root.mkdir()
    fixture = root / "_ws_n2_violation_fixture.py"
    fixture.write_text("WorldModel\n", encoding="utf-8")

    assert _world_model_identifier_offenders((root,)) == []
