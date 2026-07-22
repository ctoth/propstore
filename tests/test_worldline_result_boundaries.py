"""The worldline document boundary rejects malformed stored payloads.

Deep review F3 asked for hard failure at the worldline document boundary rather
than silent coercion (a non-mapping collection being filtered away, a scalar
being split into characters). That guarantee is unchanged; its *owner* moved.
The worldline charter now declares typed fields, so Quire's strict document
codec is what rejects a malformed payload — there is no hand-written
``from_mapping`` to validate by hand, and therefore no second spelling of the
render types to keep in sync.

These tests drive the real decode path (``convert_document_value``), which is
exactly what the family store calls when it loads a stored worldline.
"""

import pytest
from quire.documents import DocumentSchemaError, convert_document_value

from propstore.worldline.query import WorldlineResult
from propstore.worldline.result_types import WorldlineArgumentationState


def _decode(payload: object, document_type: type) -> object:
    return convert_document_value(payload, document_type, source="worldline")


def test_input_source_rejects_non_mapping_inputs_used() -> None:
    with pytest.raises(DocumentSchemaError, match="inputs_used"):
        _decode(
            {
                "values": {
                    "target": {"status": "derived", "inputs_used": []},
                }
            },
            WorldlineResult,
        )


def test_input_source_rejects_non_mapping_nested_input() -> None:
    with pytest.raises(DocumentSchemaError, match="inputs_used"):
        _decode(
            {
                "values": {
                    "target": {
                        "status": "derived",
                        "inputs_used": {"x": "not a source"},
                    },
                }
            },
            WorldlineResult,
        )


def test_target_value_rejects_non_mapping_variable_refs() -> None:
    with pytest.raises(DocumentSchemaError, match="variables"):
        _decode(
            {
                "values": {
                    "target": {
                        "status": "derived",
                        "variables": [{"name": "x"}, "not a variable"],
                    },
                }
            },
            WorldlineResult,
        )


def test_argumentation_state_rejects_wrong_top_level_type() -> None:
    with pytest.raises(DocumentSchemaError):
        _decode([], WorldlineArgumentationState)


def test_argumentation_state_rejects_wrong_mapping_field_type() -> None:
    with pytest.raises(DocumentSchemaError, match="acceptance_probs"):
        _decode({"acceptance_probs": []}, WorldlineArgumentationState)


def test_wellformed_result_decodes_to_the_canonical_types() -> None:
    result = convert_document_value(
        {
            "computed": "2026-07-13T00:00:00Z",
            "content_hash": "abc",
            "values": {
                "category": {"status": "determined", "value": "fast"},
                "enabled": {"status": "determined", "value": True},
                "count": {"status": "determined", "value": 2},
                "ratio": {"status": "determined", "value": 2.5},
            },
        },
        WorldlineResult,
        source="worldline",
    )
    assert isinstance(result, WorldlineResult)
    assert all(value.status == "determined" for value in result.values.values())
    assert type(result.values["category"].value) is str
    assert type(result.values["enabled"].value) is bool
    assert type(result.values["count"].value) is int
    assert type(result.values["ratio"].value) is float
