"""Architecture boundary: description-kind DATA must not depend on the
argumentation engine; the render-time coreference consumer is where the boundary
is crossed.

Coreference is resolved by Dung argumentation, but the description-claim / merge
-argument DATA layer must stay engine-free so storage never depends on a
reasoning surface. The crossing happens only in the dedicated render-time
``coreference`` module, which imports the ``argumentation`` package directly (a
call across the boundary, not an adapter).
"""

from __future__ import annotations

import ast
from pathlib import Path

import propstore.core.lemon.coreference as coreference_module
import propstore.core.lemon.description_kinds as description_kinds_module


def _imported_roots(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_description_kinds_does_not_import_argumentation() -> None:
    path = Path(description_kinds_module.__file__)
    assert "argumentation" not in _imported_roots(path)


def test_coreference_consumer_imports_argumentation_directly() -> None:
    path = Path(coreference_module.__file__)
    assert "argumentation" in _imported_roots(path)


def test_temporal_consumes_condition_ir_directly() -> None:
    import propstore.core.lemon.temporal as temporal_module

    path = Path(temporal_module.__file__)
    assert "condition_ir" in _imported_roots(path)
