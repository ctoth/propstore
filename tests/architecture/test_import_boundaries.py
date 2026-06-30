"""Standing architecture gate: the one-way layer dependency contract holds.

PLAN.md §12.1 carry-forward: wire the import-linter layer contract as a binding
CI gate. This test runs the committed ``.importlinter`` contracts and fails if any
layering edge is violated — a render -> world -> ... -> storage one-way stack plus
the substrate-boundary rule that ``storage`` and ``core`` never import the
argumentation / world / cli layers.

If this test goes red, fix the offending import; do not weaken the contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

from importlinter.api import use_cases

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _REPO_ROOT / ".importlinter"
_PACKAGE = _REPO_ROOT / "propstore"


def test_importlinter_config_exists() -> None:
    assert _CONFIG.exists(), "the .importlinter layer contract must be committed"


def test_layer_contracts_hold() -> None:
    kept = use_cases.lint_imports(config_filename=str(_CONFIG), cache_dir=None)

    assert kept, "import-linter layer/substrate contracts are broken (see output above)"


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _layer_imports(layer: str) -> set[str]:
    found: set[str] = set()
    for path in (_PACKAGE / layer).rglob("*.py"):
        found |= _module_imports(path)
    return found


def _imports_into(layer: str, target: str) -> set[str]:
    prefix = f"propstore.{target}"
    return {
        imported
        for imported in _layer_imports(layer)
        if imported == prefix or imported.startswith(f"{prefix}.")
    }


def test_storage_never_imports_world() -> None:
    # The lead-named binding invariant, asserted directly (independent of the
    # import-linter run) so it is unmissable.
    assert _imports_into("storage", "world") == set()


def test_core_never_imports_world() -> None:
    assert _imports_into("core", "world") == set()
