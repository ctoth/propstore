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
    old_storage_nested = ROOT / "propstore" / "storage" / "repository.py"

    assert canonical.exists()
    assert not old_nested.exists()
    assert not old_storage_nested.exists()

    offenders = [
        _relative(path)
        for path in _production_files()
        if _imports_module(_parse(path), "propstore.repo.repository")
        or _imports_module(_parse(path), "propstore.storage.repository")
    ]

    assert offenders == []


def test_propstore_git_carrier_is_not_named_knowledge_repo() -> None:
    offenders: list[tuple[str, int]] = []
    for path in _production_files():
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.ClassDef) and node.name == "KnowledgeRepo":
                offenders.append((_relative(path), node.lineno))

    assert offenders == []


def test_storage_package_exports_policy_constructors_not_gitstore_shim() -> None:
    path = ROOT / "propstore" / "storage" / "__init__.py"
    contents = path.read_text(encoding="utf-8")

    assert "GitStore" not in contents
    assert "init_git_store" in contents
    assert "open_git_store" in contents
    assert "KnowledgeRepo" not in contents


def test_git_storage_surface_is_not_named_repo_or_gitstore_shim() -> None:
    storage = ROOT / "propstore" / "storage" / "__init__.py"
    old_repo_package = ROOT / "propstore" / "repo"

    assert storage.exists()
    assert not old_repo_package.exists()

    contents = storage.read_text(encoding="utf-8")
    assert "GitStore" not in contents
    assert "init_git_store" in contents
    assert "open_git_store" in contents
    assert "KnowledgeRepo" not in contents


def test_propstore_artifacts_do_not_reexport_quire_store_shims() -> None:
    artifacts_init = ROOT / "propstore" / "artifacts" / "__init__.py"
    artifacts_policy = ROOT / "propstore" / "artifacts" / "policy.py"
    artifacts_store = ROOT / "propstore" / "artifacts" / "store.py"
    old_transaction = ROOT / "propstore" / "artifacts" / "transaction.py"
    old_types = ROOT / "propstore" / "artifacts" / "types.py"

    assert not artifacts_policy.exists()
    assert not artifacts_store.exists()
    assert not old_transaction.exists()
    assert not old_types.exists()
    assert not artifacts_init.exists()


def test_propstore_storage_snapshot_does_not_accept_bare_gitstore() -> None:
    path = ROOT / "propstore" / "storage" / "snapshot.py"
    contents = path.read_text(encoding="utf-8")
    tree = _parse(path)

    assert "SimpleNamespace" not in contents
    assert "for_git" not in contents

    class_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }
    assert "RepositorySnapshot" in class_names


def test_propstore_artifact_store_factory_is_deleted() -> None:
    path = ROOT / "propstore" / "artifacts" / "policy.py"
    repository = ROOT / "propstore" / "repository.py"
    contents = repository.read_text(encoding="utf-8")

    assert not path.exists()
    assert "create_artifact_store_for_git" not in contents
    assert "def create_artifact_store" not in contents
    assert "def artifacts" not in contents
    assert "SimpleNamespace" not in contents
    assert "def _family_store" in contents


def test_production_imports_do_not_use_propstore_repo_package() -> None:
    offenders: list[str] = []
    for path in _production_files():
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "propstore.repo" or node.module.startswith("propstore.repo."):
                    offenders.append(_relative(path))
                    break
            if isinstance(node, ast.Import):
                if any(
                    alias.name == "propstore.repo" or alias.name.startswith("propstore.repo.")
                    for alias in node.names
                ):
                    offenders.append(_relative(path))
                    break

    assert offenders == []


def test_production_public_types_do_not_use_repo_prefix() -> None:
    offenders: list[tuple[str, int, str]] = []
    for path in _production_files():
        for node in ast.walk(_parse(path)):
            if (
                isinstance(node, ast.ClassDef)
                and node.name.startswith("Repo")
                and not node.name.startswith("Repository")
            ):
                offenders.append((_relative(path), node.lineno, node.name))

    assert offenders == []


def test_current_docs_do_not_name_deleted_repo_storage_surface() -> None:
    docs = [
        ROOT / "CLAUDE.md",
        ROOT / "docs" / "git-backend.md",
        ROOT / "docs" / "semantic-merge.md",
        ROOT / "tests" / "test_repo_branch.py",
    ]
    deleted_package = "propstore" + "/repo"
    old_public_type = "Repo" + "MergeFramework"
    offenders: list[tuple[str, str]] = []

    for path in docs:
        text = path.read_text(encoding="utf-8")
        if deleted_package in text:
            offenders.append((_relative(path), deleted_package))
        if old_public_type in text:
            offenders.append((_relative(path), old_public_type))

    assert offenders == []


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

    text = path.read_text(encoding="utf-8")
    assert direct_decode_calls == []
    assert "load_document_dir(concepts_root, ConceptDocument)" in text
