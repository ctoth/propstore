from __future__ import annotations

import json
from pathlib import Path

from ast_equiv import canonical_dump


ROOT = Path(__file__).resolve().parents[1]


def _read_repo_file(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_T_extract_free_variables_replaces_broad_name_subtraction() -> None:
    source = _read_repo_file("propstore/families/claims/passes/checks.py")

    assert "extract_free_variables" in source
    assert "extract_names" not in source
    assert "KNOWN_BUILTINS" not in source


def test_T_value_resolver_dead_sympy_exception_path_deleted() -> None:
    source = _read_repo_file("propstore/world/value_resolver.py")

    assert "AstToSympyError" not in source
    assert "RecursionError" in source


def test_T_algorithm_presentation_paths_catch_recursion_without_bytecode_tier() -> None:
    app_source = _read_repo_file("propstore/app/claims.py")
    detector_source = _read_repo_file("propstore/conflict_detector/algorithms.py")

    assert "except RecursionError" in app_source
    assert "Tier.BYTECODE" not in detector_source
    assert "if result.equivalent:" in detector_source


def test_T_canonical_dump_golden_uses_versioned_ast_key() -> None:
    golden = json.loads(
        (ROOT / "tests/__resources__/ws_o_ast_canonical_dump_golden.json").read_text(
            encoding="utf-8"
        )
    )

    assert canonical_dump(golden["body"], golden["bindings"]) == golden["canonical_dump"]
    assert golden["canonical_dump"].startswith("1:")
