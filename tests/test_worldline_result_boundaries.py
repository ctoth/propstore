import pytest

from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineInputSource,
    WorldlineTargetValue,
)


def test_input_source_rejects_non_mapping_inputs_used():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineInputSource.from_mapping({"source": "derived", "inputs_used": []})


def test_input_source_rejects_non_mapping_nested_input():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineInputSource.from_mapping(
            {"source": "derived", "inputs_used": {"x": "not a source"}}
        )


def test_target_value_rejects_non_mapping_inputs_used():
    with pytest.raises(ValueError, match="inputs_used"):
        WorldlineTargetValue.from_mapping({"status": "derived", "inputs_used": []})


def test_target_value_rejects_non_mapping_variable_refs():
    with pytest.raises(ValueError, match="variables"):
        WorldlineTargetValue.from_mapping(
            {"status": "derived", "variables": [{"name": "x"}, "not a variable"]}
        )


def test_argumentation_state_rejects_wrong_top_level_type():
    with pytest.raises(ValueError, match="argumentation"):
        WorldlineArgumentationState.from_mapping([])


def test_argumentation_state_rejects_wrong_mapping_field_type():
    with pytest.raises(ValueError, match="acceptance_probs"):
        WorldlineArgumentationState.from_mapping({"acceptance_probs": []})
