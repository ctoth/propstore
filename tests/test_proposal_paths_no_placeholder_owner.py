from __future__ import annotations

import ast
from pathlib import Path

from propstore.proposals import stance_proposal_branch, stance_proposal_relpath


def test_proposal_path_helpers_do_not_fabricate_repository_owner() -> None:
    source = Path("propstore/proposals.py").read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        assert not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
            and len(node.args) == 2
            and isinstance(node.args[1], ast.Call)
            and isinstance(node.args[1].func, ast.Name)
            and node.args[1].func.id == "object"
        )

    assert "typing import TYPE_CHECKING, cast" not in source
    assert stance_proposal_branch() == "proposal/stances"
    assert stance_proposal_relpath("paper:claim_a") == "stances/paper__claim_a.yaml"
