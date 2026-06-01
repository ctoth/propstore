from __future__ import annotations


import pytest
import yaml

from propstore.families.concepts.types import ConceptRelationshipType
from propstore.families.concepts.types import ConceptStatus
from propstore.core.graph_relation_types import GraphRelationType
from tests.family_helpers import materialized_world_store_path
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.world import WorldQuery
from tests.conftest import (
    normalize_claims_payload,
    normalize_concept_payloads,
    write_test_context,
)


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


def test_build_compiled_world_graph_preserves_sidecar_rows(graph_build_world) -> None:
    from propstore.core.graph_build import build_compiled_world_graph

    graph = build_compiled_world_graph(graph_build_world)

    assert {concept.concept_id for concept in graph.concepts} == {
        _concept_artifact("concept1"),
        _concept_artifact("concept2"),
        _concept_artifact("concept3"),
        _concept_artifact("concept4"),
    }
    assert {claim.claim_id for claim in graph.claims} == {
        "graph_build_test:claim_mass",
        "graph_build_test:claim_accel",
        "graph_build_test:claim_force_a",
        "graph_build_test:claim_force_b",
    }
    assert any(
        relation.provenance is not None
        and relation.provenance.source_table == "relationship"
        and relation.relation_type is GraphRelationType.BROADER
        for relation in graph.relations
    )
    assert any(
        relation.provenance is not None
        and relation.provenance.source_table == "relation_edge"
        and relation.relation_type is GraphRelationType.REBUTS
        for relation in graph.relations
    )
    assert graph.parameterizations == (graph.parameterizations[0],)
    assert graph.parameterizations[0].output_concept_id == _concept_artifact("concept3")
    assert graph.parameterizations[0].input_concept_ids == (
        _concept_artifact("concept1"),
        _concept_artifact("concept2"),
    )
    assert {graph.conflicts[0].left_claim_id, graph.conflicts[0].right_claim_id} == {
        "graph_build_test:claim_force_a",
        "graph_build_test:claim_force_b",
    }


def test_build_compiled_world_graph_carries_relation_opinion(graph_build_world) -> None:
    from propstore.core.graph_build import build_compiled_world_graph
    from propstore.opinion import Opinion

    opinion = Opinion(0.7, 0.1, 0.2, 0.5)

    class OpinionStore:
        def __init__(self, base) -> None:
            self._base = base

        def all_concepts(self):
            return self._base.all_concepts()

        def claims_for(self, concept_id):
            return self._base.claims_for(concept_id)

        def all_parameterizations(self):
            return self._base.all_parameterizations()

        def all_relationships(self):
            return self._base.all_relationships()

        def all_claim_stances(self):
            rows = list(self._base.all_claim_stances())
            rows[0].opinion = opinion
            return rows

        def conflicts(self, concept_id=None):
            return self._base.conflicts(concept_id)

    graph = build_compiled_world_graph(OpinionStore(graph_build_world))

    stance_edges = [
        relation
        for relation in graph.relations
        if relation.relation_type is GraphRelationType.REBUTS
    ]
    assert stance_edges
    assert stance_edges[0].opinion is opinion


def test_world_relationship_rows_use_concept_relationship_enum(
    graph_build_world,
) -> None:
    relationships = graph_build_world.all_relationships()

    assert relationships
    assert any(
        relationship.relation_type == ConceptRelationshipType.BROADER.value
        for relationship in relationships
    )


def test_world_concept_rows_use_concept_status_enum(graph_build_world) -> None:
    concepts = graph_build_world.all_concepts()

    assert concepts
    assert any(concept.status == ConceptStatus.ACCEPTED.value for concept in concepts)


def test_build_compiled_world_graph_is_row_order_independent(graph_build_world) -> None:
    from propstore.core.graph_build import build_compiled_world_graph

    class ReversedStore:
        def __init__(self, base) -> None:
            self._base = base

        def all_concepts(self) -> list[dict]:
            return list(reversed(self._base.all_concepts()))

        def claims_for(self, concept_id):
            assert concept_id is None
            return list(reversed(self._base.claims_for(concept_id)))

        def all_parameterizations(self) -> list[dict]:
            return list(reversed(self._base.all_parameterizations()))

        def all_relationships(self) -> list[dict]:
            return list(reversed(self._base.all_relationships()))

        def all_claim_stances(self) -> list[dict]:
            return list(reversed(self._base.all_claim_stances()))

        def conflicts(self, concept_id=None) -> list[dict]:
            assert concept_id is None
            return list(reversed(self._base.conflicts(concept_id)))

    original = build_compiled_world_graph(graph_build_world)
    reversed_rows = build_compiled_world_graph(ReversedStore(graph_build_world))

    assert reversed_rows == original


def test_world_query_compiled_graph_hook_is_stable(graph_build_world) -> None:
    first = graph_build_world.compiled_graph()
    second = graph_build_world.compiled_graph()

    assert first == second
    assert first is not second
