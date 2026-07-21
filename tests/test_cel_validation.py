"""CEL validation: identifier extraction + the structural-concept invariant.

The compiler's structural-invariant pre-pass aborts only on a *structural*
concept appearing in a CEL expression — a narrow architectural invariant. Ordinary
CEL type errors are NOT this pass's concern (they quarantine through the claim
pipeline). These tests pin both the narrow detection and the generic identifier
walk it rests on.
"""

from __future__ import annotations

import pytest
from condition_ir import ConceptInfo, KindType

from propstore.cel_validation import (
    CelExpressionLocation,
    CelIngestValidationError,
    iter_cel_identifiers,
    iter_claim_condition_expressions,
    iter_context_assumption_expressions,
    structural_concepts_in_expression,
    validate_cel_expression,
    validate_cel_expressions,
)


def _registry() -> dict[str, ConceptInfo]:
    return {
        "freq": ConceptInfo(
            id="freq", canonical_name="frequency", kind=KindType.QUANTITY
        ),
        "onset": ConceptInfo(
            id="onset", canonical_name="onset", kind=KindType.TIMEPOINT
        ),
        "shape": ConceptInfo(
            id="shape", canonical_name="shape", kind=KindType.STRUCTURAL
        ),
    }


def test_iter_cel_identifiers_collects_names() -> None:
    assert iter_cel_identifiers("freq > 10 && onset < 5") == frozenset(
        {"freq", "onset"}
    )


def test_iter_cel_identifiers_handles_nested_call() -> None:
    assert "freq" in iter_cel_identifiers("(freq + 1) > 10")


def test_iter_cel_identifiers_on_parse_error_is_empty() -> None:
    # A syntactically invalid expression is general claim semantic invalidity,
    # quarantined elsewhere — the structural pre-pass sees no identifiers.
    assert iter_cel_identifiers("freq > ") == frozenset()


def test_structural_concept_detected() -> None:
    assert structural_concepts_in_expression("shape == 1", _registry()) == ("shape",)


def test_non_structural_expression_has_no_structural_concepts() -> None:
    assert structural_concepts_in_expression("freq > 10", _registry()) == ()


def test_validate_cel_expression_passes_clean() -> None:
    location = CelExpressionLocation(
        artifact_label="claim 'c1'", field="condition", index=0
    )
    validate_cel_expression("freq > 10", _registry(), location=location)


def test_validate_cel_expression_raises_on_type_error() -> None:
    location = CelExpressionLocation(
        artifact_label="claim 'c1'", field="condition", index=0
    )
    with pytest.raises(CelIngestValidationError) as excinfo:
        validate_cel_expression("freq > 'abc'", _registry(), location=location)
    assert "claim 'c1'" in str(excinfo.value)


def test_validate_cel_expressions_is_fail_fast() -> None:
    items = iter_claim_condition_expressions(
        ["freq > 10", "freq > 'abc'", "onset < 5"], artifact_label="claim 'c1'"
    )
    with pytest.raises(CelIngestValidationError):
        validate_cel_expressions(items, _registry())


def test_iter_claim_condition_expressions_locations() -> None:
    pairs = list(
        iter_claim_condition_expressions(["a", "b"], artifact_label="claim 'c1'")
    )
    assert [(p[0], p[1].field, p[1].index) for p in pairs] == [
        ("a", "condition", 0),
        ("b", "condition", 1),
    ]


def test_iter_context_assumption_expressions_locations() -> None:
    pairs = list(
        iter_context_assumption_expressions(["x"], artifact_label="context 'ctx1'")
    )
    assert pairs[0][1].field == "assumption"
    assert pairs[0][1].render() == "context 'ctx1': assumption[0]"
