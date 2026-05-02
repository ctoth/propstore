from __future__ import annotations

from pathlib import Path


DOC_PATHS = (
    Path("docs/cel-typed-expressions.md"),
    Path("docs/conflict-detection.md"),
    Path("docs/data-model.md"),
    Path("docs/python-api.md"),
    Path("docs/argumentation-package-boundary.md"),
    Path("README.md"),
)


def test_condition_docs_name_target_condition_surface() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in DOC_PATHS
        if path.exists()
    )

    assert "propstore.core.conditions" in combined
    assert "ConditionSolver" in combined
    assert "CheckedCondition" in combined
    assert "ConditionIR" in combined


def test_condition_docs_do_not_advertise_deleted_condition_surfaces() -> None:
    offenders: dict[str, list[str]] = {}
    forbidden = ("propstore.z3_conditions", "z3_conditions.py", "CheckedCelExpr")
    for path in DOC_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        hits = [token for token in forbidden if token in text]
        if hits:
            offenders[str(path)] = hits

    assert offenders == {}
