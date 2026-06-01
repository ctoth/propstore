import pytest

from propstore.core.environment import Environment
from propstore.core.graph_types import WorldActivationGraph
from propstore.world.types import (
    IntegrityConstraintKind,
    RenderPolicy,
    integrity_constraint_from_dict,
)
from propstore.world.resolution import ClaimProvenance
from propstore.worldline.definition import WorldlineInputs, WorldlineResult


def test_environment_rejects_wrong_top_level_type():
    with pytest.raises(ValueError, match="environment"):
        Environment.from_dict([])


def test_environment_rejects_malformed_bindings():
    with pytest.raises(ValueError, match="bindings"):
        Environment.from_dict({"bindings": []})


def test_active_world_graph_rejects_malformed_compiled_graph():
    with pytest.raises(ValueError, match="compiled"):
        WorldActivationGraph.from_dict({"compiled": []})


def test_render_policy_rejects_malformed_map_fields():
    with pytest.raises(ValueError, match="overrides"):
        RenderPolicy.from_dict({"overrides": []})

    with pytest.raises(ValueError, match="concept_strategies"):
        RenderPolicy.from_dict({"concept_strategies": []})


def test_integrity_constraint_rejects_malformed_metadata():
    with pytest.raises(ValueError, match="metadata"):
        integrity_constraint_from_dict(
            {
                "kind": IntegrityConstraintKind.CEL.value,
                "concept_ids": ["x"],
                "metadata": [],
            }
        )


def test_claim_provenance_rejects_malformed_json_object():
    with pytest.raises(ValueError, match="provenance"):
        ClaimProvenance.from_components(provenance_json="[]")

    with pytest.raises(ValueError, match="provenance"):
        ClaimProvenance.from_components(provenance_json="{not json")


def test_worldline_inputs_rejects_malformed_overrides():
    with pytest.raises(ValueError, match="overrides"):
        WorldlineInputs.from_dict({"overrides": []})


def test_worldline_result_rejects_malformed_values():
    with pytest.raises(ValueError, match="values"):
        WorldlineResult.from_dict({"values": []})

    with pytest.raises(ValueError, match=r"\$\.values"):
        WorldlineResult.from_dict({"values": {"target": []}})
