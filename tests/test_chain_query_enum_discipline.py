"""Structural enforcement: chain_query must compare ValueStatus by identity.

`ValueStatus` is a `StrEnum`, so `status == "determined"` silently returns
True for enum members — a behavioral test cannot detect drift back to bare
strings. This AST-level test pins the invariant by walking the `chain_query`
method body and forbidding any `node.status == "literal"` comparison.
"""

from __future__ import annotations

import ast
from pathlib import Path

import propstore.world.model as world_model


def test_chain_query_status_comparisons_use_enum_identity() -> None:
    source_path = Path(world_model.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    chain_query_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "chain_query"
    ]
    # The free function carries the resolution logic; the repo-backed reader's
    # ``WorldQuery.chain_query`` method delegates to it. The enum-identity
    # discipline applies to every ``chain_query`` definition.
    assert chain_query_nodes, "no chain_query definition found in world.model"

    offenders: list[tuple[int, str]] = []
    for chain_query in chain_query_nodes:
        for node in ast.walk(chain_query):
            if not isinstance(node, ast.Compare):
                continue
            if not isinstance(node.left, ast.Attribute) or node.left.attr != "status":
                continue
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(
                    comparator.value, str
                ):
                    offenders.append((node.lineno, comparator.value))

    assert offenders == [], (
        f"chain_query compares .status against bare strings: {offenders}. "
        f"Use `is ValueStatus.X` identity comparison instead."
    )
