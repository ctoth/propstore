import pytest

from propstore.core.claim_values import ClaimProvenance
from propstore.core.environment import Environment
from propstore.core.graph_types import ActiveWorldGraph
from propstore.support_revision.explanation_types import RevisionExplanation
from propstore.support_revision.snapshot_types import (
    EpistemicStateSnapshot,
    RevisionEpisodeSnapshot,
)
from propstore.world.types import (
    IntegrityConstraintKind,
    RenderPolicy,
    integrity_constraint_from_dict,
)
from propstore.worldline.definition import WorldlineInputs, WorldlineResult
from propstore.worldline.revision_types import (
    RevisionConflictSelection,
    WorldlineRevisionState,
)


def test_environment_rejects_wrong_top_level_type():
    with pytest.raises(ValueError, match="environment"):
        Environment.from_dict([])


def test_environment_rejects_malformed_bindings():
    with pytest.raises(ValueError, match="bindings"):
        Environment.from_dict({"bindings": []})


def test_active_world_graph_rejects_malformed_compiled_graph():
    with pytest.raises(ValueError, match="compiled"):
        ActiveWorldGraph.from_dict({"compiled": []})


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

    with pytest.raises(ValueError, match="values.target"):
        WorldlineResult.from_dict({"values": {"target": []}})


def test_revision_conflicts_reject_wrong_top_level_type():
    with pytest.raises(ValueError, match="conflicts"):
        RevisionConflictSelection.from_mapping([])


def test_worldline_revision_state_rejects_malformed_nested_blocks():
    with pytest.raises(ValueError, match="result"):
        WorldlineRevisionState.from_mapping({"operation": "revise", "result": []})

    with pytest.raises(ValueError, match="state"):
        WorldlineRevisionState.from_mapping({"operation": "revise", "state": []})


def test_revision_explanation_rejects_malformed_atoms():
    with pytest.raises(ValueError, match="atoms"):
        RevisionExplanation.from_mapping(
            {"accepted_atom_ids": [], "rejected_atom_ids": [], "atoms": []}
        )

    with pytest.raises(ValueError, match="atoms.claim:1"):
        RevisionExplanation.from_mapping(
            {
                "accepted_atom_ids": [],
                "rejected_atom_ids": [],
                "atoms": {"claim:1": []},
            }
        )


def test_support_revision_snapshots_reject_malformed_maps():
    with pytest.raises(ValueError, match="explanation"):
        RevisionEpisodeSnapshot.from_mapping(
            {
                "operator": "revise",
                "explanation": [],
            }
        )

    with pytest.raises(ValueError, match="support_sets"):
        EpistemicStateSnapshot.from_mapping(
            {
                "scope": {"bindings": {}},
                "base": {
                    "scope": {"bindings": {}},
                    "atoms": [],
                    "assumptions": [],
                    "support_sets": [],
                    "essential_support": {},
                },
                "accepted_atom_ids": [],
                "ranked_atom_ids": [],
            }
        )

    with pytest.raises(ValueError, match="ranking"):
        EpistemicStateSnapshot.from_mapping(
            {
                "scope": {"bindings": {}},
                "base": {
                    "scope": {"bindings": {}},
                    "atoms": [],
                    "assumptions": [],
                    "support_sets": {},
                    "essential_support": {},
                },
                "accepted_atom_ids": [],
                "ranked_atom_ids": [],
                "ranking": [],
            }
        )
