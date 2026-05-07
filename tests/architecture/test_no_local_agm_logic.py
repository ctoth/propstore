from __future__ import annotations

import ast
from pathlib import Path


DECISION_OWNER_MODULES = (
    Path("propstore/support_revision/operators.py"),
    Path("propstore/support_revision/iterated.py"),
    Path("propstore/support_revision/entrenchment.py"),
)

FORBIDDEN_FORMAL_TERMS = (
    "lexicographic",
    "restrained",
    "partial meet",
    "remainder",
    "sphere",
    "IC merge",
    "Delta",
    "Levi",
    "Harper",
)

FORBIDDEN_LOCAL_FUNCTIONS = {
    Path("propstore/support_revision/operators.py"): {
        "_choose_incision_set",
    },
    Path("propstore/support_revision/iterated.py"): {
        "_updated_entrenchment_report",
    },
}


def _string_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _defined_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def test_support_revision_decision_modules_do_not_name_formal_kernels() -> None:
    """Phase 0/close guard: fails before WS-AGM Phase 4/5/6 cutover.

    Formal AGM, iterated revision, entrenchment, and IC merge decisions belong
    to ``belief_set``. These support-revision modules may realize support-level
    consequences, but they must not contain local formal-kernel vocabulary.
    """

    offenders: list[str] = []
    for path in DECISION_OWNER_MODULES:
        text_literals = _string_literals(path)
        for literal in text_literals:
            for term in FORBIDDEN_FORMAL_TERMS:
                if term.lower() in literal.lower():
                    offenders.append(f"{path}: literal contains {term!r}: {literal!r}")

    assert offenders == []


def test_support_revision_decision_modules_do_not_define_local_decision_helpers() -> None:
    """Phase 0/close guard for local formal-decision helper families."""

    offenders: list[str] = []
    for path, forbidden_names in FORBIDDEN_LOCAL_FUNCTIONS.items():
        defined = _defined_functions(path)
        offenders.extend(f"{path}: {name}" for name in sorted(defined & forbidden_names))

    assert offenders == []
