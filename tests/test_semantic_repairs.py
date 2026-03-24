from __future__ import annotations

import pytest
import yaml

from propstore.argumentation import compute_claim_graph_justified_claims
from propstore.build_sidecar import build_sidecar
from propstore.cli.repository import Repository
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.world import ResolutionStrategy, WorldModel, resolve


def _build_world(tmp_path, concepts: list[dict], claim_docs: list[dict]) -> WorldModel:
    root = tmp_path / "knowledge"
    concepts_dir = root / "concepts"
    claims_dir = root / "claims"
    forms_dir = root / "forms"
    counters_dir = concepts_dir / ".counters"

    concepts_dir.mkdir(parents=True)
    claims_dir.mkdir()
    forms_dir.mkdir()
    counters_dir.mkdir()
    (counters_dir / "semantic.next").write_text("10")

    form_names = {concept["form"] for concept in concepts}
    for form_name in sorted(form_names):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name}, default_flow_style=False)
        )

    for concept in concepts:
        (concepts_dir / f"{concept['canonical_name']}.yaml").write_text(
            yaml.dump(concept, default_flow_style=False)
        )

    for index, claim_doc in enumerate(claim_docs, start=1):
        (claims_dir / f"claims_{index}.yaml").write_text(
            yaml.dump(claim_doc, default_flow_style=False)
        )

    repo = Repository(root)
    loaded_concepts = load_concepts(repo.concepts_dir)
    loaded_claims = load_claim_files(repo.claims_dir)
    concept_registry = {
        concept.data["id"]: concept.data
        for concept in loaded_concepts
        if concept.data.get("id")
    }
    build_sidecar(
        loaded_concepts,
        repo.sidecar_path,
        claim_files=loaded_claims,
        concept_registry=concept_registry,
        repo=repo,
    )
    return WorldModel(repo)


@pytest.fixture
def argumentation_world(tmp_path):
    concepts = [
        {
            "id": "concept1",
            "canonical_name": "target_value",
            "status": "accepted",
            "definition": "Target concept with conflicting local claims.",
            "domain": "semantic",
            "form": "frequency",
        },
        {
            "id": "concept2",
            "canonical_name": "external_evidence",
            "status": "accepted",
            "definition": "External claim that attacks one local claimant.",
            "domain": "semantic",
            "form": "structural",
        },
        {
            "id": "concept3",
            "canonical_name": "task",
            "status": "accepted",
            "definition": "Execution context.",
            "domain": "semantic",
            "form": "category",
            "form_parameters": {"values": ["speech"], "extensible": False},
        },
    ]
    claim_docs = [{
        "source": {"paper": "semantic_argumentation"},
        "claims": [
            {
                "id": "target_a",
                "type": "parameter",
                "concept": "concept1",
                "value": 1.0,
                "conditions": ["task == 'speech'"],
            },
            {
                "id": "target_b",
                "type": "parameter",
                "concept": "concept1",
                "value": 2.0,
                "conditions": ["task == 'speech'"],
                "stances": [{"type": "supersedes", "target": "target_a"}],
            },
            {
                "id": "external_c",
                "type": "observation",
                "statement": "External evidence defeats target_b.",
                "concepts": ["concept2"],
                "conditions": ["task == 'speech'"],
                "stances": [{"type": "supersedes", "target": "target_b"}],
            },
        ],
    }]

    world = _build_world(tmp_path, concepts, claim_docs)
    try:
        yield world
    finally:
        world.close()


@pytest.fixture
def derivation_world(tmp_path):
    concepts = [
        {
            "id": "concept1",
            "canonical_name": "a_input",
            "status": "accepted",
            "definition": "First input.",
            "domain": "semantic",
            "form": "frequency",
        },
        {
            "id": "concept2",
            "canonical_name": "b_input",
            "status": "accepted",
            "definition": "Conflicted input.",
            "domain": "semantic",
            "form": "frequency",
        },
        {
            "id": "concept3",
            "canonical_name": "c_input",
            "status": "accepted",
            "definition": "Fallback input.",
            "domain": "semantic",
            "form": "frequency",
        },
        {
            "id": "concept4",
            "canonical_name": "d_input",
            "status": "accepted",
            "definition": "Fallback input.",
            "domain": "semantic",
            "form": "frequency",
        },
        {
            "id": "concept5",
            "canonical_name": "derived_target",
            "status": "accepted",
            "definition": "Target concept with two parameterizations.",
            "domain": "semantic",
            "form": "frequency",
            "parameterization_relationships": [
                {
                    "formula": "x = a + b",
                    "sympy": "Eq(concept5, concept1 + concept2)",
                    "inputs": ["concept1", "concept2"],
                    "exactness": "exact",
                    "source": "conflicted-first",
                    "bidirectional": True,
                    "conditions": ["task == 'speech'"],
                },
                {
                    "formula": "x = c * d",
                    "sympy": "Eq(concept5, concept3 * concept4)",
                    "inputs": ["concept3", "concept4"],
                    "exactness": "exact",
                    "source": "viable-second",
                    "bidirectional": True,
                    "conditions": ["task == 'speech'"],
                },
            ],
        },
        {
            "id": "concept6",
            "canonical_name": "task",
            "status": "accepted",
            "definition": "Execution context.",
            "domain": "semantic",
            "form": "category",
            "form_parameters": {"values": ["speech"], "extensible": False},
        },
    ]
    claim_docs = [{
        "source": {"paper": "semantic_derivation"},
        "claims": [
            {
                "id": "a_value",
                "type": "parameter",
                "concept": "concept1",
                "value": 10.0,
                "conditions": ["task == 'speech'"],
            },
            {
                "id": "b_value_1",
                "type": "parameter",
                "concept": "concept2",
                "value": 1.0,
                "conditions": ["task == 'speech'"],
            },
            {
                "id": "b_value_2",
                "type": "parameter",
                "concept": "concept2",
                "value": 2.0,
                "conditions": ["task == 'speech'"],
            },
            {
                "id": "c_value",
                "type": "parameter",
                "concept": "concept3",
                "value": 3.0,
                "conditions": ["task == 'speech'"],
            },
            {
                "id": "d_value",
                "type": "parameter",
                "concept": "concept4",
                "value": 4.0,
                "conditions": ["task == 'speech'"],
            },
        ],
    }]

    world = _build_world(tmp_path, concepts, claim_docs)
    try:
        yield world
    finally:
        world.close()


def test_argumentation_resolution_uses_whole_active_belief_space(argumentation_world):
    bound = argumentation_world.bind(task="speech")

    local_only = compute_claim_graph_justified_claims(argumentation_world, {"target_a", "target_b"})
    assert local_only == frozenset({"target_b"})

    result = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=argumentation_world,
    )

    assert result.status == "resolved"
    assert result.winning_claim_id == "target_a"


def test_derived_value_checks_all_compatible_parameterizations(derivation_world):
    bound = derivation_world.bind(task="speech")

    result = bound.derived_value("concept5")

    assert result.status == "derived"
    assert result.value == pytest.approx(12.0)
    assert result.formula == "x = c * d"
