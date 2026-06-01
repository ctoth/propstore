"""Tests for graph_export — KnowledgeGraph construction and serialization."""

import sqlite3

import pytest
import yaml

from tests.family_helpers import (
    materialized_world_store_path,
    world_query_from_sqlite_path,
)
from propstore.world.graph_projection import project_knowledge_graph
from propstore.families.identity.concepts import derive_concept_artifact_id
from tests.sidecar_schema_helpers import build_world_projection_schema
from propstore.world import WorldQuery
from tests.conftest import (
    normalize_claims_payload,
    normalize_concept_payloads,
    write_test_context,
)


# ── Fixtures (duplicated from test_world_query.py) ────────────────────


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


@pytest.fixture
def repo(concept_dir):
    from propstore.repository import Repository

    return Repository(concept_dir.parent)


@pytest.fixture
def world(concept_dir, repo, claim_files):
    """Build sidecar and return a WorldQuery."""
    materialized_world_store_path(repo)
    return WorldQuery(repo)


# ── Tests ─────────────────────────────────────────────────────────────


class TestUnboundGraph:
    def test_unbound_graph_has_all_concepts(self, world):
        """All 7 concepts appear as nodes."""
        graph = project_knowledge_graph(world)
        concept_nodes = [n for n in graph.nodes if n.node_type == "concept"]
        concept_ids = {n.id for n in concept_nodes}
        for i in range(1, 8):
            artifact_id = _concept_artifact(f"concept{i}")
            assert artifact_id in concept_ids, f"{artifact_id} missing from graph"
        assert len(concept_nodes) == 7

    def test_unbound_graph_has_parameterization_edges(self, world):
        """concept6->concept5 and concept1->concept5 parameterization edges exist."""
        graph = project_knowledge_graph(world)
        param_edges = [e for e in graph.edges if e.edge_type == "parameterization"]
        # concept5 has inputs [concept6, concept1]
        param_targets = {(e.source, e.target) for e in param_edges}
        assert (
            _concept_artifact("concept6"),
            _concept_artifact("concept5"),
        ) in param_targets
        assert (
            _concept_artifact("concept1"),
            _concept_artifact("concept5"),
        ) in param_targets

    def test_unbound_graph_has_relationship_edges(self, world):
        """concept1->concept4 broader edge exists."""
        graph = project_knowledge_graph(world)
        rel_edges = [e for e in graph.edges if e.edge_type == "relationship"]
        rel_pairs = {(e.source, e.target) for e in rel_edges}
        assert (
            _concept_artifact("concept1"),
            _concept_artifact("concept4"),
        ) in rel_pairs

    def test_unbound_graph_has_stance_edges(self, world):
        """claim2->claim1 rebuts edge exists."""
        graph = project_knowledge_graph(world)
        stance_edges = [e for e in graph.edges if e.edge_type == "stance"]
        stance_pairs = {(e.source, e.target) for e in stance_edges}
        assert ("claim2", "claim1") in stance_pairs


class TestBoundGraph:
    def test_bound_graph_filters_claims(self, world):
        """Under singing binding, only singing claims appear."""
        bound = world.bind(task="singing")
        graph = project_knowledge_graph(world, bound=bound)
        claim_nodes = [n for n in graph.nodes if n.node_type == "claim"]
        claim_ids = {n.id for n in claim_nodes}
        # claim3 is the singing claim for concept1
        assert "claim3" in claim_ids
        # speech-only claims should not be present
        assert "claim1" not in claim_ids
        assert "claim2" not in claim_ids


class TestGroupScoping:
    def test_group_scoping(self, world):
        """group_id filters to concepts in that group only."""
        concept5 = _concept_artifact("concept5")
        gid = next(
            (
                group_id
                for group_id in range(len(world.all_concepts()))
                if concept5 in world.concept_ids_for_group(group_id)
            ),
            None,
        )
        assert gid is not None, "concept5 should be in a parameterization group"

        graph = project_knowledge_graph(world, group_id=gid)
        concept_nodes = [n for n in graph.nodes if n.node_type == "concept"]
        concept_ids = {n.id for n in concept_nodes}

        # concept5, concept6, concept1, concept7 should be in the group
        # (connected via parameterization)
        assert _concept_artifact("concept5") in concept_ids
        # Concepts outside the group should be excluded
        assert _concept_artifact("concept3") not in concept_ids


class TestSerialization:
    def test_to_dot_valid(self, world):
        """Output contains 'digraph', node and edge declarations."""
        graph = project_knowledge_graph(world)
        dot = graph.to_dot()
        assert "digraph" in dot
        # Should contain at least one node reference
        assert _concept_artifact("concept1") in dot
        # Should contain edge declarations (->)
        assert "->" in dot

    def test_to_json_structure(self, world):
        """Output has nodes/edges keys, each node has id/label/node_type."""
        graph = project_knowledge_graph(world)
        result = graph.to_json()
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) > 0
        for node in result["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "node_type" in node
            assert "metadata" in node


class TestConflictedClaims:
    def test_conflicted_claims_marked(self, world):
        """Under speech, concept1 claims marked as conflicted."""
        bound = world.bind(task="speech")
        graph = project_knowledge_graph(world, bound=bound)
        # Find claim nodes for concept1
        concept1_claims = [
            n
            for n in graph.nodes
            if n.node_type == "claim"
            and n.metadata.get("concept_id") == _concept_artifact("concept1")
        ]
        assert len(concept1_claims) > 0
        for claim_node in concept1_claims:
            assert claim_node.metadata.get("status") == "conflicted", (
                f"{claim_node.id} should be marked conflicted under speech"
            )
