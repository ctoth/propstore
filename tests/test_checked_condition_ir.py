from __future__ import annotations

import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.core.conditions import (
    CheckedCondition,
    ConditionBinary,
    ConditionLiteral,
    ConditionSourceSpan,
    ConditionValueKind,
    check_condition_ir,
    checked_condition_set,
)


def test_cel_frontend_returns_checked_condition_ir() -> None:
    checked = check_condition_ir("temperature > 21", _registry())

    assert checked.source == "temperature > 21"
    assert isinstance(checked.ir, ConditionBinary)
    assert checked.registry_fingerprint.startswith("sha256:")
    assert checked.warnings == ()
    assert not hasattr(checked, "ast")


def test_checked_condition_preserves_frontend_warnings() -> None:
    checked = check_condition_ir("task == 'dancing'", _registry())

    assert len(checked.warnings) == 1
    assert "not in value set" in checked.warnings[0]


def test_checked_condition_set_deduplicates_and_sorts_by_source() -> None:
    span = ConditionSourceSpan(0, 1)
    left = CheckedCondition(
        source="b == true",
        ir=ConditionLiteral(True, ConditionValueKind.BOOLEAN, span),
        registry_fingerprint="sha256:registry",
    )
    right = CheckedCondition(
        source="a == true",
        ir=ConditionLiteral(True, ConditionValueKind.BOOLEAN, span),
        registry_fingerprint="sha256:registry",
    )

    condition_set = checked_condition_set((left, right, left))

    assert condition_set.sources == ("a == true", "b == true")
    assert condition_set.registry_fingerprint == "sha256:registry"


def test_checked_condition_rejects_empty_registry_fingerprint() -> None:
    with pytest.raises(ValueError, match="registry fingerprint"):
        CheckedCondition(
            source="ok",
            ir=ConditionLiteral(True, ConditionValueKind.BOOLEAN, ConditionSourceSpan(0, 2)),
            registry_fingerprint="",
        )


def _registry() -> dict[str, ConceptInfo]:
    return {
        "temperature": ConceptInfo(
            id="ps:concept:temperature",
            canonical_name="temperature",
            kind=KindType.QUANTITY,
        ),
        "task": ConceptInfo(
            id="ps:concept:task",
            canonical_name="task",
            kind=KindType.CATEGORY,
            category_values=["speech"],
            category_extensible=True,
        ),
    }
