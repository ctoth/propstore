from __future__ import annotations

import ast
from pathlib import Path


PROHIBITED_SUBTREES = (
    Path("propstore/context_lifting.py"),
    Path("propstore/aspic_bridge"),
    Path("propstore/grounding"),
)
ALLOWED_BELIEF_SET_IMPORT_OWNER = "propstore.support_revision.belief_set_adapter"


def _module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def _imports_belief_set(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "belief_set" or alias.name.startswith("belief_set.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module == "belief_set" or node.module.startswith("belief_set."):
                return True
    return False


def _production_python_files(root: Path = Path("propstore")) -> list[Path]:
    return [
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and path.exists()
    ]


def test_lifting_argumentation_and_grounding_do_not_import_belief_set() -> None:
    """AGM/IC papers in ../belief-set/papers define a separate formal
    belief-dynamics dependency. They are excluded from the McCarthy/Guha
    `ist(c,p)` projection path; this regression guard passes at Phase 0.
    """

    offenders: list[str] = []
    for subtree in PROHIBITED_SUBTREES:
        paths = [subtree] if subtree.is_file() else list(subtree.rglob("*.py"))
        offenders.extend(str(path) for path in paths if _imports_belief_set(path))

    assert offenders == []


def test_belief_set_import_edges_are_only_formal_revision_adapters() -> None:
    """Positive boundary: propstore has exactly one formal belief-set adapter.

    Formal AGM and IC merge live in the sibling belief_set package. Propstore
    may import that package only through this adapter; every other production
    module must call propstore owner-layer APIs instead of reaching across the
    dependency boundary directly.
    """

    edges = [
        _module_name(path)
        for path in _production_python_files()
        if _imports_belief_set(path)
    ]

    assert edges == [ALLOWED_BELIEF_SET_IMPORT_OWNER]
