"""WS-J Step 8/J-M5: blocked lifting exceptions are worldline dependencies."""

from __future__ import annotations

from propstore.context_lifting import (
    LiftingException,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.world.types import Environment
from propstore.world.bound import BoundWorld
from propstore.worldline import WorldlineDefinition, WorldlineInputs, run_worldline
from propstore.worldline.result_types import WorldlineDependencies


def test_ws_j_worldline_dependencies_roundtrip_lifting_provenance() -> None:
    dependencies = WorldlineDependencies.from_mapping(
        {
            "claims": ["claim_local"],
            "contexts": ["ctx_target"],
            "lifting_rules": ["lift-source-target"],
            "blocked_exceptions": ["except-alpha"],
        }
    )

    assert dependencies.lifting_rules == ("lift-source-target",)
    assert dependencies.blocked_exceptions == ("except-alpha",)
    assert dependencies.to_dict()["lifting_rules"] == ["lift-source-target"]
    assert dependencies.to_dict()["blocked_exceptions"] == ["except-alpha"]


def test_ws_j_worldline_dependencies_include_blocked_lifting_exception() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    lifting_system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
        ),
        lifting_exceptions=(
            LiftingException(
                id="except-alpha",
                rule_id="lift-source-target",
                target=target,
                proposition_id="claim_alpha",
                clashing_set=("ctx_target:claim_local",),
            ),
        ),
    )

    class _Store:
        def __init__(self) -> None:
            from propstore.z3_conditions import Z3ConditionSolver

            self._solver = Z3ConditionSolver({})
            self._claims = {
                "claim_alpha": {
                    "id": "claim_alpha",
                    "concept_id": "concept:target",
                    "value": 12.0,
                    "context_id": "ctx_source",
                },
                "claim_local": {
                    "id": "claim_local",
                    "concept_id": "concept:target",
                    "value": 42.0,
                    "context_id": "ctx_target",
                },
            }

        def bind(self, environment=None, *, policy=None, **conditions):
            return BoundWorld(
                self,
                environment=environment,
                policy=policy,
                lifting_system=lifting_system,
            )

        def resolve_concept(self, name):
            return "concept:target" if name == "target" else None

        def get_concept(self, concept_id):
            if concept_id == "concept:target":
                return {"id": "concept:target", "canonical_name": "target"}
            return None

        def get_claim(self, claim_id):
            return self._claims.get(claim_id)

        def claims_for(self, concept_id):
            return [
                claim
                for claim in self._claims.values()
                if concept_id is None or claim.get("concept_id") == concept_id
            ]

        def condition_solver(self):
            return self._solver

        def has_table(self, name):
            return False

        def parameterizations_for(self, concept_id):
            return []

    definition = WorldlineDefinition(
        id="blocked_lifting_provenance",
        targets=["target"],
        inputs=WorldlineInputs(environment=Environment(context_id="ctx_target")),
    )

    result = run_worldline(definition, _Store())

    assert result.dependencies.lifting_rules == ("lift-source-target",)
    assert result.dependencies.blocked_exceptions == ("except-alpha",)
