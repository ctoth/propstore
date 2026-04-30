from __future__ import annotations

from ast_equiv.comparison import Tier


def test_workstream_o_ast_done() -> None:
    assert {tier.name for tier in Tier} == {
        "NONE",
        "CANONICAL",
        "SYMPY",
        "PARTIAL_EVAL",
    }
