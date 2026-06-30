"""Graph export — KnowledgeGraph construction and DOT/JSON serialization.

Rewrite-native port of the reference ``test_graph_export.py`` (``docs/rewrite/
deferred-tests.md`` world export-graph row). The reference is ``*Row``-shaped over
a hand-authored projection; these author the ONE canonical charters
(``Repository.init`` -> ``repo.families.*.save`` -> ``WorldQuery``) and read the
graph the world store exposes. Concept/claim ids are the authored logical ids, so
node ids are ``"c1"`` / ``"cl1"`` directly, with no artifact-id round-trip.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from condition_ir import KindType

from propstore.core.lemon import LexicalEntry
from propstore.core.lemon.forms import LexicalForm
from propstore.core.lemon.references import OntologyReference
from propstore.core.lemon.types import LexicalSense
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.families.relations import Stance
from propstore.graph_export import (
    GraphExportRequest,
    KnowledgeGraph,
    build_knowledge_graph,
    export_knowledge_graph,
)
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.world import WorldQuery


def _gate_concept() -> Concept:
    entry = LexicalEntry(
        identifier="gate",
        canonical_form=LexicalForm(written_rep="gate", language="en"),
        senses=(LexicalSense(reference=OntologyReference(uri="ex:gate", label="gate")),),
        physical_dimension_form="freq",
    )
    return Concept(concept_id="gate", canonical_name="gate", lexical_entry=entry)


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")
    repo.families.form.save(
        "freq",
        FormDefinition(name="freq", kind=KindType.QUANTITY, unit_symbol="Hz"),
        message="m",
    )
    repo.families.concept.save("gate", _gate_concept(), message="m")
    for cid, name in (
        ("c1", "fundamental_frequency"),
        ("c2", "subglottal_pressure"),
        ("c5", "return_phase_ratio"),
        ("c6", "return_phase_time"),
    ):
        repo.families.concept.save(
            cid, Concept(concept_id=cid, canonical_name=name), message="m"
        )

    # Two conflicting parameter claims for c1 (no conditions -> always active).
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=200.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=350.0,
        ),
        message="m",
    )
    # A condition-gated parameter claim for c2 (active only under region == 'eu').
    repo.families.claim.save(
        "cl_eu",
        Claim(
            claim_id="cl_eu",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c2",
            value=800.0,
            conditions=["gate > 100"],
        ),
        message="m",
    )
    # An equation claim c5 <- (c6, c1): one parameterization group {c5, c6, c1}.
    repo.families.claim.save(
        "eq1",
        Claim(
            claim_id="eq1",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            output_concept="c5",
            concepts=["c6", "c1"],
            expression="c5 = c6 * c1",
        ),
        message="m",
    )
    # A stance: cl2 rebuts cl1.
    repo.families.stance.save(
        "s1",
        Stance(
            stance_id="s1",
            source_claim_id="cl2",
            target_claim_id="cl1",
            stance_type=StanceType.REBUTS,
        ),
        message="m",
    )
    return repo


@pytest.fixture
def world(tmp_path: Path) -> WorldQuery:
    return WorldQuery(_repo(tmp_path))


class TestUnboundGraph:
    def test_all_concepts_are_nodes(self, world: WorldQuery) -> None:
        graph = build_knowledge_graph(world)
        concept_ids = {n.id for n in graph.nodes if n.node_type == "concept"}
        assert concept_ids == {"gate", "c1", "c2", "c5", "c6"}

    def test_claim_nodes_present_with_value_labels(self, world: WorldQuery) -> None:
        graph = build_knowledge_graph(world)
        claim_nodes = {n.id: n for n in graph.nodes if n.node_type == "claim"}
        assert {"cl1", "cl2", "cl_eu", "eq1"} <= set(claim_nodes)
        assert claim_nodes["cl1"].label == "cl1=200.0"

    def test_parameterization_edges(self, world: WorldQuery) -> None:
        graph = build_knowledge_graph(world)
        param = {(e.source, e.target) for e in graph.edges if e.edge_type == "parameterization"}
        assert ("c6", "c5") in param
        assert ("c1", "c5") in param

    def test_stance_edge(self, world: WorldQuery) -> None:
        graph = build_knowledge_graph(world)
        stance = {(e.source, e.target) for e in graph.edges if e.edge_type == "stance"}
        assert ("cl2", "cl1") in stance

    def test_claim_of_edges(self, world: WorldQuery) -> None:
        graph = build_knowledge_graph(world)
        claim_of = {(e.source, e.target) for e in graph.edges if e.edge_type == "claim_of"}
        assert ("cl1", "c1") in claim_of
        assert ("cl_eu", "c2") in claim_of

    def test_relationship_edges_honest_empty(self, world: WorldQuery) -> None:
        # Concept-to-concept relations are not a stored family in the rewrite.
        graph = build_knowledge_graph(world)
        assert [e for e in graph.edges if e.edge_type == "relationship"] == []


class TestBoundGraph:
    def test_bound_graph_filters_inactive_claims(self, world: WorldQuery) -> None:
        bound = world.bind(gate=50.0)
        graph = build_knowledge_graph(world, bound=bound)
        claim_ids = {n.id for n in graph.nodes if n.node_type == "claim"}
        # cl_eu is gated to gate > 100; under gate == 50 it is inactive.
        assert "cl_eu" not in claim_ids
        assert "cl1" in claim_ids

    def test_bound_graph_includes_active_conditional_claim(self, world: WorldQuery) -> None:
        bound = world.bind(gate=200.0)
        graph = build_knowledge_graph(world, bound=bound)
        claim_ids = {n.id for n in graph.nodes if n.node_type == "claim"}
        assert "cl_eu" in claim_ids


class TestGroupScoping:
    def test_group_scoping_restricts_concepts(self, world: WorldQuery) -> None:
        # Only outputs are graph nodes; c5's inputs (c6, c1) are not themselves
        # equation outputs, so the single parameterization group is {c5}.
        assert set(world.group_members("c5")) == {"c5"}
        graph = build_knowledge_graph(world, group_id=0)
        concept_ids = {n.id for n in graph.nodes if n.node_type == "concept"}
        assert "c5" in concept_ids
        # Concepts in no parameterization group are excluded from the scoped graph.
        assert "c2" not in concept_ids
        assert "gate" not in concept_ids


class TestConflictMarking:
    def test_conflicted_claims_marked(self, world: WorldQuery) -> None:
        bound = world.bind()
        graph = build_knowledge_graph(world, bound=bound)
        c1_claims = [
            n
            for n in graph.nodes
            if n.node_type == "claim" and n.metadata.get("concept_id") == "c1"
        ]
        assert {n.id for n in c1_claims} == {"cl1", "cl2"}
        for node in c1_claims:
            assert node.metadata.get("status") == "conflicted"


class TestSerialization:
    def test_to_dot_valid(self, world: WorldQuery) -> None:
        dot = build_knowledge_graph(world).to_dot()
        assert "digraph" in dot
        assert "c1" in dot
        assert "->" in dot

    def test_to_json_structure(self, world: WorldQuery) -> None:
        result = build_knowledge_graph(world).to_json()
        assert set(result) == {"nodes", "edges"}
        assert result["nodes"]
        for node in result["nodes"]:
            assert {"id", "label", "node_type", "metadata"} <= set(node)


class TestExportRequest:
    def test_export_knowledge_graph_unbound(self, world: WorldQuery) -> None:
        report = export_knowledge_graph(world, GraphExportRequest())
        assert isinstance(report.graph, KnowledgeGraph)
        assert {n.id for n in report.graph.nodes if n.node_type == "concept"} == {
            "gate",
            "c1",
            "c2",
            "c5",
            "c6",
        }

    def test_export_knowledge_graph_bound_filters(self, world: WorldQuery) -> None:
        report = export_knowledge_graph(
            world, GraphExportRequest(bindings={"gate": 50.0})
        )
        claim_ids = {n.id for n in report.graph.nodes if n.node_type == "claim"}
        assert "cl_eu" not in claim_ids
