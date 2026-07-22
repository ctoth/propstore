"""Categorical parameterization providers remain visible in the ATMS."""

from __future__ import annotations

from pathlib import Path

from propstore.core.environment import Environment
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.world import WorldQuery
from propstore.world.types import ATMSNodeStatus, ATMSOutKind


def test_ws_i_categorical_provider_creates_visible_rejected_derived_node(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.concept.save(
        "category_input",
        Concept(concept_id="category_input", canonical_name="category_input"),
        message="add categorical input",
    )
    repo.families.concept.save(
        "numeric_output",
        Concept(concept_id="numeric_output", canonical_name="numeric_output"),
        message="add numeric output",
    )
    repo.families.context.save(
        "ctx",
        Context(context_id="ctx", name="test context"),
        message="add context",
    )
    repo.families.claim.save(
        "categorical_provider",
        Claim(
            claim_id="categorical_provider",
            context_id="ctx",
            claim_type=ClaimType.PARAMETER,
            output_concept="category_input",
            value="red",
        ),
        message="add categorical provider",
    )
    repo.families.claim.save(
        "numeric_equation",
        Claim(
            claim_id="numeric_equation",
            context_id="ctx",
            claim_type=ClaimType.EQUATION,
            output_concept="numeric_output",
            concepts=("category_input",),
            expression="category_input",
            sympy="category_input",
        ),
        message="add numeric equation",
    )

    with WorldQuery(repo) as world:
        engine = world.bind(Environment()).atms_engine()
        rejection_value = (
            "parameterization_input_type_incompatible:"
            "0:category_input:categorical_provider"
        )
        rejection_node_id = engine._derived_node_id("numeric_output", rejection_value)
        rejection = engine.node_status(rejection_node_id)

    assert rejection.kind == "derived"
    assert rejection.status is ATMSNodeStatus.OUT
    assert rejection.out_kind is ATMSOutKind.PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE
    assert rejection.reason is not None
    assert "category_input from categorical_provider has str value" in rejection.reason
