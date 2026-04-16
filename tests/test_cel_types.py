import pytest

from propstore.cel_checker import (
    BinaryOpNode,
    CheckedCelExpr,
    ConceptInfo,
    KindType,
    cel_registry_fingerprint,
    check_cel_condition_set,
    check_cel_expr,
    parse_cel_expr,
)
from propstore.cel_types import (
    CelRegistryFingerprint,
    CheckedCelConditionSet,
    CelExpr,
    to_cel_expr,
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


def test_parse_cel_expr_returns_source_and_ast():
    parsed = parse_cel_expr(CelExpr("x > 1"))

    assert parsed.source == "x > 1"
    assert isinstance(parsed.ast, BinaryOpNode)


def test_checked_cel_expr_requires_checker_construction(registry):
    parsed = parse_cel_expr("x > 1")

    with pytest.raises(TypeError, match="must be created by the CEL checker"):
        CheckedCelExpr(
            source=parsed.source,
            ast=parsed.ast,
            registry_fingerprint=cel_registry_fingerprint(registry),
        )


def test_check_cel_expr_carries_ast_fingerprint_and_warnings(registry):
    checked = check_cel_expr("task == 'novel'", registry)

    assert checked.source == "task == 'novel'"
    assert isinstance(checked.ast, BinaryOpNode)
    assert checked.registry_fingerprint == cel_registry_fingerprint(registry)
    assert len(checked.warnings) == 1


def test_check_cel_expr_rejects_hard_errors(registry):
    with pytest.raises(ValueError, match="Undefined concept"):
        check_cel_expr("missing > 1", registry)


def test_registry_fingerprint_changes_with_cel_semantics(registry):
    changed = dict(registry)
    changed["task"] = ConceptInfo(
        "ps:concept:task",
        "task",
        KindType.CATEGORY,
        category_values=["speech"],
        category_extensible=False,
    )

    assert cel_registry_fingerprint(registry) != cel_registry_fingerprint(changed)


def test_checked_condition_set_normalizes_and_deduplicates(registry):
    condition_set = check_cel_condition_set(
        [CelExpr("task == 'speech'"), CelExpr("x > 1"), CelExpr("x > 1")],
        registry,
    )

    assert condition_set.sources == ("task == 'speech'", "x > 1")
    assert condition_set.registry_fingerprint == cel_registry_fingerprint(registry)


def test_checked_condition_set_rejects_mixed_registry_fingerprints(registry):
    checked = check_cel_expr("x > 1", registry)

    with pytest.raises(ValueError, match="registry fingerprint"):
        CheckedCelConditionSet(
            conditions=(checked,),
            registry_fingerprint=CelRegistryFingerprint("other"),
        )

