from __future__ import annotations

import json

import pytest
import yaml

from propstore.build_sidecar import build_sidecar
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.world import WorldModel


@pytest.fixture
def graph_build_world(tmp_path):
    knowledge = tmp_path / "knowledge"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    claims_dir = knowledge / "claims"
    concepts_dir.mkdir(parents=True)
    forms_dir.mkdir()
    claims_dir.mkdir()

    counters = concepts_dir / ".counters"
    counters.mkdir()
    (counters / "physics.next").write_text("10", encoding="utf-8")

    for form_name, form_data in {
        "mass": {"name": "mass", "kind": "quantity", "dimensionless": False},
        "acceleration": {"name": "acceleration", "kind": "quantity", "dimensionless": False},
        "force": {"name": "force", "kind": "quantity", "dimensionless": False},
        "category": {"name": "category", "kind": "category"},
    }.items():
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump(form_data, default_flow_style=False),
            encoding="utf-8",
        )

    concept_payloads = {
        "mass": {
            "id": "concept1",
            "canonical_name": "mass",
            "status": "accepted",
            "definition": "Mass.",
            "form": "mass",
        },
        "acceleration": {
            "id": "concept2",
            "canonical_name": "acceleration",
            "status": "accepted",
            "definition": "Acceleration.",
            "form": "acceleration",
        },
        "force": {
            "id": "concept3",
            "canonical_name": "force",
            "status": "accepted",
            "definition": "Force.",
            "form": "force",
            "relationships": [
                {"type": "broader", "target": "concept1"},
            ],
            "parameterization_relationships": [
                {
                    "formula": "F = m * a",
                    "inputs": ["concept1", "concept2"],
                    "sympy": "Eq(concept3, concept1 * concept2)",
                    "exactness": "exact",
                    "source": "Newton",
                    "bidirectional": True,
                    "conditions": ["task == 'speech'"],
                }
            ],
        },
        "task": {
            "id": "concept4",
            "canonical_name": "task",
            "status": "accepted",
            "definition": "Task.",
            "form": "category",
            "form_parameters": {"values": ["speech", "singing"], "extensible": False},
        },
    }

    for name, payload in concept_payloads.items():
        (concepts_dir / f"{name}.yaml").write_text(
            yaml.dump(payload, default_flow_style=False),
            encoding="utf-8",
        )

    claims_payload = {
        "source": {"paper": "graph_build_test"},
        "claims": [
            {
                "id": "claim_mass",
                "type": "parameter",
                "concept": "concept1",
                "value": 5.0,
                "unit": "kg",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "graph_build_test", "page": 1},
            },
            {
                "id": "claim_accel",
                "type": "parameter",
                "concept": "concept2",
                "value": 2.0,
                "unit": "m/s^2",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "graph_build_test", "page": 2},
            },
            {
                "id": "claim_force_a",
                "type": "parameter",
                "concept": "concept3",
                "value": 10.0,
                "unit": "N",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "graph_build_test", "page": 3},
            },
            {
                "id": "claim_force_b",
                "type": "parameter",
                "concept": "concept3",
                "value": 12.0,
                "unit": "N",
                "conditions": ["task == 'speech'"],
                "provenance": {"paper": "graph_build_test", "page": 4},
                "stances": [
                    {
                        "type": "rebuts",
                        "target": "claim_force_a",
                        "strength": "strong",
                        "note": "conflicting direct measurement",
                    }
                ],
            },
        ],
    }
    (claims_dir / "claims.yaml").write_text(
        yaml.dump(claims_payload, default_flow_style=False),
        encoding="utf-8",
    )

    from propstore.cli.repository import Repository

    repo = Repository(knowledge)
    concepts = load_concepts(repo.concepts_dir)
    claim_files = load_claim_files(repo.claims_dir)
    build_sidecar(concepts, repo.sidecar_path, claim_files=claim_files, repo=repo)
    return WorldModel(repo)


def test_build_compiled_world_graph_preserves_sidecar_rows(graph_build_world) -> None:
    from propstore.core.graph_build import build_compiled_world_graph

    graph = build_compiled_world_graph(graph_build_world)

    assert {concept.concept_id for concept in graph.concepts} == {
        "concept1",
        "concept2",
        "concept3",
        "concept4",
    }
    assert {claim.claim_id for claim in graph.claims} == {
        "claim_mass",
        "claim_accel",
        "claim_force_a",
        "claim_force_b",
    }
    assert any(
        relation.provenance is not None
        and relation.provenance.source_table == "relationship"
        and relation.relation_type == "broader"
        for relation in graph.relations
    )
    assert any(
        relation.provenance is not None
        and relation.provenance.source_table == "claim_stance"
        and relation.relation_type == "rebuts"
        for relation in graph.relations
    )
    assert graph.parameterizations == (
        graph.parameterizations[0],
    )
    assert graph.parameterizations[0].output_concept_id == "concept3"
    assert graph.parameterizations[0].input_concept_ids == ("concept1", "concept2")
    assert {graph.conflicts[0].left_claim_id, graph.conflicts[0].right_claim_id} == {
        "claim_force_a",
        "claim_force_b",
    }


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


def test_world_model_compiled_graph_hook_is_stable(graph_build_world) -> None:
    first = graph_build_world.compiled_graph()
    second = graph_build_world.compiled_graph()

    assert first == second
    assert first is not second
