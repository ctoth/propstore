from __future__ import annotations

import pytest
import yaml

from propstore.claim_graph import compute_claim_graph_justified_claims
from propstore.families.claims.types import ClaimType
from tests.family_helpers import materialized_world_store_path
from propstore.world import ResolutionStrategy, WorldQuery, resolve
from propstore.world.queries import world_claim_display_id
from propstore.world.value_resolver import ClaimValueResolver
from tests.conftest import (
    normalize_claims_payload,
    normalize_concept_payloads,
    write_test_context,
)
from tests.claim_model_helpers import make_claim


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
    claim_docs = [
        {
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
        }
    ]

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
    claim_docs = [
        {
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
        }
    ]

    world = _build_world(tmp_path, concepts, claim_docs)
    try:
        yield world
    finally:
        world.close()


def test_argumentation_resolution_uses_whole_active_belief_space(argumentation_world):
    bound = argumentation_world.bind(task="speech")

    local_only = compute_claim_graph_justified_claims(
        argumentation_world, {"target_a", "target_b"}
    )
    assert local_only == frozenset({"target_b"})

    result = resolve(
        bound,
        "concept1",
        ResolutionStrategy.ARGUMENTATION,
        world=argumentation_world,
    )

    assert result.status == "resolved"
    assert result.winning_claim_id is not None
    winning_claim = argumentation_world.get_claim(result.winning_claim_id)
    assert winning_claim is not None
    assert world_claim_display_id(winning_claim) == "semantic_argumentation:target_a"


def test_derived_value_checks_all_compatible_parameterizations(derivation_world):
    bound = derivation_world.bind(task="speech")

    result = bound.derived_value("concept5")

    assert result.status == "derived"
    assert result.value == pytest.approx(12.0)
    assert result.formula == "x = c * d"


def test_mixed_direct_and_multistatement_algorithm_uses_ast_equivalence():
    resolver = ClaimValueResolver(
        parameterizations_for=lambda cid: [],
        is_param_compatible=lambda conds: True,
        value_of=lambda cid: None,
        extract_variable_concepts=lambda claim: [
            str(variable.concept_id)
            for variable in claim.variables
            if variable.concept_id is not None
        ],
        collect_known_values=lambda ids: {"input": 5.0},
        extract_bindings=lambda claim: claim.variable_bindings(),
    )

    active = [
        make_claim(
            "direct",
            claim_type=ClaimType.PARAMETER,
            value=10.0,
        ),
        make_claim(
            "algo",
            claim_type=ClaimType.ALGORITHM,
            value=None,
            algorithm_body="def compute(x):\n    y = x * 2\n    return y\n",
            variables_json='[{"name":"x","concept":"input"}]',
        ),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status == "determined"
