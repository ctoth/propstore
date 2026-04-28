from __future__ import annotations

import ast
import inspect
import textwrap

from propstore.storage.snapshot import RepositorySnapshot


def test_materialize_clean_collects_deletions_before_unlinking() -> None:
    source = inspect.getsource(RepositorySnapshot._clean_materialized_semantic_files)
    tree = ast.parse(textwrap.dedent(source))

    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        call = node.iter
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "rglob"
        ):
            assert not any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "unlink"
                for child in ast.walk(node)
            )
