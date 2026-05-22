import pytest

from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineInputSource,
    WorldlineStep,
    WorldlineTargetValue,
)


def test_input_source_rejects_non_mapping_inputs_used():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineInputSource.from_json_payload({"source": "derived", "inputs_used": []})


def test_input_source_rejects_non_mapping_nested_input():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineInputSource.from_json_payload(
            {"source": "derived", "inputs_used": {"x": "not a source"}}
        )


def test_input_source_rejects_non_scalar_value():
    with pytest.raises(ValueError, match="value"):
        WorldlineInputSource.from_json_payload(
            {"source": "derived", "value": {"not": "scalar"}}
        )


def test_target_value_rejects_non_mapping_inputs_used():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineTargetValue.from_json_payload({"status": "derived", "inputs_used": []})


def test_target_value_rejects_non_mapping_variable_refs():
    with pytest.raises(ValueError, match="variables"):
        WorldlineTargetValue.from_json_payload(
            {"status": "derived", "variables": [{"name": "x"}, "not a variable"]}
        )


def test_target_value_rejects_non_scalar_value():
    with pytest.raises(ValueError, match="value"):
        WorldlineTargetValue.from_json_payload(
            {"status": "determined", "value": ["not", "scalar"]}
        )


def test_step_rejects_non_scalar_value():
    with pytest.raises(ValueError, match="value"):
        WorldlineStep.from_json_payload(
            {"concept": "force", "source": "derived", "value": {"not": "scalar"}}
        )


def test_argumentation_state_rejects_wrong_top_level_type():
    with pytest.raises(ValueError, match="argumentation"):
        WorldlineArgumentationState.from_json_payload([])


def test_argumentation_state_rejects_wrong_mapping_field_type():
    with pytest.raises(ValueError, match="acceptance_probs"):
        WorldlineArgumentationState.from_json_payload({"acceptance_probs": []})
