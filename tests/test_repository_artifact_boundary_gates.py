from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROPSTORE = ROOT / "propstore"


def _production_files() -> list[Path]:
    return sorted(
        path
        for path in PROPSTORE.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _imports_module(tree: ast.AST, module_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == module_name:
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module_name or alias.name.startswith(f"{module_name}."):
                    return True
    return False


def test_non_cli_production_modules_do_not_import_cli_repository() -> None:
    offenders = [
        _relative(path)
        for path in _production_files()
        if not _relative(path).startswith("propstore/cli/")
        and _imports_module(_parse(path), "propstore.cli.repository")
    ]

    assert offenders == []


def test_cli_repository_module_no_longer_defines_repository_facade() -> None:
    path = ROOT / "propstore" / "cli" / "repository.py"
    if not path.exists():
        return

    class_names = {
        node.name
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.ClassDef)
    }

    assert "Repository" not in class_names
    assert "RepositoryNotFound" not in class_names


def test_repository_facade_does_not_depend_on_world_model() -> None:
    candidates = [
        ROOT / "propstore" / "repository.py",
        ROOT / "propstore" / "repo" / "repository.py",
    ]
    repository_modules = [path for path in candidates if path.exists()]
    assert repository_modules != []

    for path in repository_modules:
        tree = _parse(path)
        assert not _imports_module(tree, "propstore.world")
        assert not _imports_module(tree, "propstore.world.model")
        store_defs = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "store"
        ]
        assert store_defs == []


def test_repository_facade_has_single_canonical_import_surface() -> None:
    canonical = ROOT / "propstore" / "repository.py"
    old_nested = ROOT / "propstore" / "repo" / "repository.py"

    assert canonical.exists()
    assert not old_nested.exists()

    offenders = [
        _relative(path)
        for path in _production_files()
        if _imports_module(_parse(path), "propstore.repo.repository")
    ]

    assert offenders == []


def test_propstore_git_carrier_is_not_named_knowledge_repo() -> None:
    offenders: list[tuple[str, int]] = []
    for path in _production_files():
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.ClassDef) and node.name == "KnowledgeRepo":
                offenders.append((_relative(path), node.lineno))

    assert offenders == []


def test_repo_package_exports_git_store_not_knowledge_repo() -> None:
    path = ROOT / "propstore" / "repo" / "__init__.py"
    contents = path.read_text(encoding="utf-8")

    assert "GitStore" in contents
    assert "KnowledgeRepo" not in contents


def test_core_concept_loading_does_not_decode_concept_documents_directly() -> None:
    path = ROOT / "propstore" / "core" / "concepts.py"
    tree = _parse(path)

    direct_decode_calls: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in {"load_document", "decode_document", "decode_document_bytes"}:
            continue
        if any(isinstance(arg, ast.Name) and arg.id == "ConceptDocument" for arg in node.args):
            direct_decode_calls.append(node.lineno)

    assert direct_decode_calls == []
    assert "CONCEPT_FILE_FAMILY" in path.read_text(encoding="utf-8")
