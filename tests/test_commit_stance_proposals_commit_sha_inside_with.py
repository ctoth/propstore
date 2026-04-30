from __future__ import annotations

import ast
from pathlib import Path


def test_commit_stance_proposals_reads_commit_sha_inside_transaction_with() -> None:
    source_path = Path("propstore/proposals.py")
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "commit_stance_proposals"
    )
    transaction_with = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.With)
        and any(
            isinstance(item.optional_vars, ast.Name)
            and item.optional_vars.id == "transaction"
            for item in node.items
        )
    )

    commit_sha_reads = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Attribute)
        and node.attr == "commit_sha"
        and isinstance(node.value, ast.Name)
        and node.value.id == "transaction"
    ]

    assert commit_sha_reads
    assert all(
        transaction_with.lineno <= node.lineno <= transaction_with.end_lineno
        for node in commit_sha_reads
    )
