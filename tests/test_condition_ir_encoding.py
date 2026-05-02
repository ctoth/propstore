from __future__ import annotations

import pytest

from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionLiteral,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
)
from propstore.core.id_types import ConceptId


def test_condition_ir_codec_round_trips_all_metadata() -> None:
    from propstore.core.conditions.codec import condition_ir_from_json, condition_ir_to_json

    timepoint_kind = getattr(ConditionValueKind, "TIMEPOINT")
    condition = ConditionBinary(
        op=ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
        left=ConditionReference(
            concept_id=ConceptId("ps:concept:valid-from"),
            source_name="valid_from",
            value_kind=timepoint_kind,
            span=ConditionSourceSpan(0, 10),
        ),
        right=ConditionLiteral(
            value=100,
            value_kind=ConditionValueKind.NUMERIC,
            span=ConditionSourceSpan(14, 17),
        ),
        span=ConditionSourceSpan(0, 17),
    )

    encoded = condition_ir_to_json(condition)

    assert encoded["version"] == 1
    assert condition_ir_from_json(encoded) == condition


def test_condition_ir_codec_preserves_category_metadata() -> None:
    from propstore.core.conditions.codec import condition_ir_from_json, condition_ir_to_json

    condition = ConditionReference(
        concept_id=ConceptId("ps:concept:task"),
        source_name="task",
        value_kind=ConditionValueKind.STRING,
        span=ConditionSourceSpan(0, 4),
        category_values=("speech", "singing"),
        category_extensible=False,
    )

    encoded = condition_ir_to_json(condition)

    assert encoded["category_values"] == ["speech", "singing"]
    assert encoded["category_extensible"] is False
    assert condition_ir_from_json(encoded) == condition


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 999, "node": "literal"},
        {"version": 1, "node": "not-a-node"},
        {
            "version": 1,
            "node": "binary",
            "op": "not-an-op",
            "left": {"version": 1, "node": "literal", "value": True, "value_kind": "boolean", "span": [0, 4]},
            "right": {"version": 1, "node": "literal", "value": True, "value_kind": "boolean", "span": [0, 4]},
            "span": [0, 4],
        },
        {"version": 1, "node": "literal", "value": 1, "value_kind": "not-a-kind", "span": [0, 1]},
    ],
)
def test_condition_ir_codec_rejects_unknown_tags(payload: dict[str, object]) -> None:
    from propstore.core.conditions.codec import condition_ir_from_json

    with pytest.raises(ValueError):
        condition_ir_from_json(payload)
