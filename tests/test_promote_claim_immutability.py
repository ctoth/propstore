from __future__ import annotations

import ast
from pathlib import Path


def test_promote_source_branch_rebuilds_claim_payloads_without_in_place_mutation() -> None:
    tree = ast.parse(Path("propstore/source/promote.py").read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in {"clear", "update"}:
            continue
        if isinstance(func.value, ast.Name) and func.value.id == "claim":
            offenders.append(f"claim.{func.attr} at line {node.lineno}")

    assert offenders == []
