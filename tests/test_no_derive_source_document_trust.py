from __future__ import annotations

import ast
from pathlib import Path


def test_no_source_document_trust_derivation_function_in_propstore() -> None:
    definitions: list[str] = []
    for path in Path("propstore").rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node.name == "derive_source_document_trust"
            ):
                definitions.append(f"{path}:{node.lineno}")

    assert definitions == []


def test_heuristic_source_trust_exports_no_world_query_calibrator() -> None:
    source = Path("propstore/heuristic/source_trust.py").read_text()

    assert "derive_source_document_trust" not in source
    assert "WorldQuery" not in source
    assert "chain_query" not in source

