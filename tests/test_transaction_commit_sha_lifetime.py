from __future__ import annotations

import ast
from pathlib import Path


_SCOPED_MUTATION_FILES = (
    Path("propstore/source/finalize.py"),
    Path("propstore/source/promote.py"),
    Path("propstore/importing/repository_import.py"),
)


def test_head_bound_transaction_commit_sha_is_read_inside_context() -> None:
    offenders: list[str] = []
    for path in _SCOPED_MUTATION_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parent: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent[child] = node
        with_bodies = [
            set(ast.walk(with_node))
            for with_node in ast.walk(tree)
            if isinstance(with_node, ast.With)
            and any(_is_head_bound_transaction(item.context_expr) for item in with_node.items)
        ]
        for node in ast.walk(tree):
            if not _is_head_txn_commit_sha(node):
                continue
            if not any(node in body for body in with_bodies):
                offenders.append(f"{path}:{node.lineno}")
    assert offenders == []


def _is_head_bound_transaction(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return isinstance(func, ast.Attribute) and func.attr == "head_bound_transaction"


def _is_head_txn_commit_sha(node: ast.AST) -> bool:
    if not isinstance(node, ast.Attribute) or node.attr != "commit_sha":
        return False
    value = node.value
    return isinstance(value, ast.Name) and value.id == "head_txn"
