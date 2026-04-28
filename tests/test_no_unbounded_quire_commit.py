from __future__ import annotations

import ast
from pathlib import Path


_SCOPED_MUTATION_FILES = (
    Path("propstore/source/finalize.py"),
    Path("propstore/source/promote.py"),
    Path("propstore/storage/repository_import.py"),
    Path("propstore/storage/snapshot.py"),
)


def test_ws_q_scoped_mutation_paths_do_not_bypass_head_bound_transaction() -> None:
    violations: list[str] = []
    for path in _SCOPED_MUTATION_FILES:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if not isinstance(node, ast.Call):
                continue
            if _is_repo_families_transact_call(node):
                violations.append(f"{path}:{node.lineno} uses repo.families.transact directly")
            if _is_git_commit_call(node):
                violations.append(f"{path}:{node.lineno} uses git commit primitive directly")

    assert violations == []


def test_ws_q_scoped_mutation_paths_enter_head_bound_transaction() -> None:
    missing = [
        str(path)
        for path in _SCOPED_MUTATION_FILES
        if not _has_head_bound_transaction(path)
    ]

    assert missing == []


def _is_repo_families_transact_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "transact":
        return False
    value = func.value
    return (
        isinstance(value, ast.Attribute)
        and value.attr == "families"
        and isinstance(value.value, ast.Name)
        and value.value.id in {"repo", "repository"}
    )


def _is_git_commit_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in {"commit_batch", "commit_files", "commit_deletes", "commit_flat_tree"}:
        return False
    value = func.value
    return isinstance(value, ast.Attribute) and value.attr == "git"


def _has_head_bound_transaction(path: Path) -> bool:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "head_bound_transaction":
            return True
    return False
