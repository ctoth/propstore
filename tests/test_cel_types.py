import pytest

from propstore.cel_types import CelExpr, CelRegistryFingerprint, to_cel_expr
from propstore.core.conditions import check_condition_ir
from propstore.core.conditions.checked import (
    CheckedConditionSet,
    checked_condition_set,
)
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    condition_registry_fingerprint,
)


@pytest.fixture
def registry():
    return {
        "x": ConceptInfo("ps:concept:x", "x", KindType.QUANTITY),
        "task": ConceptInfo(
            "ps:concept:task",
            "task",
            KindType.CATEGORY,
            category_values=["speech"],
            category_extensible=True,
        ),
    }


def test_raw_cel_source_is_branded_text():
    expr = to_cel_expr("x > 1")

    assert expr == "x > 1"
    assert isinstance(expr, str)


def test_raw_cel_source_rejects_non_strings():
    with pytest.raises(TypeError, match="must be a string"):
        to_cel_expr(3)


def test_check_condition_ir_carries_source_fingerprint_and_warnings(registry):
    checked = check_condition_ir("task == 'novel'", registry)

    assert checked.source == "task == 'novel'"
    assert checked.registry_fingerprint == condition_registry_fingerprint(registry)
    assert checked.encoded_ir is not None
    assert len(checked.warnings) == 1


def test_check_condition_ir_rejects_hard_errors(registry):
    with pytest.raises(ValueError, match="Undefined concept"):
        check_condition_ir("missing > 1", registry)


def test_registry_fingerprint_changes_with_condition_semantics(registry):
    changed = dict(registry)
    changed["task"] = ConceptInfo(
        "ps:concept:task",
        "task",
        KindType.CATEGORY,
        category_values=["speech"],
        category_extensible=False,
    )

    assert condition_registry_fingerprint(registry) != condition_registry_fingerprint(changed)


def test_checked_condition_set_normalizes_and_deduplicates(registry):
    condition_set = checked_condition_set(
        [
            check_condition_ir(CelExpr("task == 'speech'"), registry),
            check_condition_ir(CelExpr("x > 1"), registry),
            check_condition_ir(CelExpr("x > 1"), registry),
        ]
    )

    assert condition_set.sources == ("task == 'speech'", "x > 1")
    assert condition_set.registry_fingerprint == condition_registry_fingerprint(registry)


def test_checked_condition_set_rejects_mixed_registry_fingerprints(registry):
    checked = check_condition_ir("x > 1", registry)

    with pytest.raises(ValueError, match="registry fingerprint"):
        CheckedConditionSet(
            conditions=(checked,),
            registry_fingerprint=CelRegistryFingerprint("other"),
        )
