from __future__ import annotations


from propstore.core.activation import activate_compiled_world_graph
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.justifications import claim_justifications_from_active_graph
from propstore.core.labels import compile_environment_assumptions
from propstore.families.claims.declaration import Claim
from propstore.families.relations.declaration import ConflictWitness, Stance
from propstore.world.types import Environment
from tests.claim_model_helpers import claim_from_test_payload


class _JustificationStore:
    def claims_for(self, concept_id: str | None) -> list[Claim]:
        if concept_id is None:
            return list(self._claim_models)
        return [
            claim
            for claim in self._claim_models
            if claim.output_concept_id == concept_id
        ]

    def stances_between(self, claim_ids: set[str]) -> list[Stance]:
        return [
            stance
            for stance in self._stances
            if stance.claim_id in claim_ids and stance.target_claim_id in claim_ids
        ]

    def all_parameterizations(self) -> list[dict]:
        return []

    def all_relationships(self) -> list[dict]:
        return []

    def conflicts(self) -> list[ConflictWitness]:
        return []

    def all_concepts(self) -> list[dict]:
        return []

    def condition_solver(self):
        class _ExactMatchSolver:
            def are_disjoint(self, left: list[str], right: list[str]) -> bool:
                return set(left).isdisjoint(right)

        return _ExactMatchSolver()


def test_claim_justifications_from_active_graph_preserves_reported_and_support_edges() -> (
    None
):
    store = _JustificationStore()
    environment = Environment(
        assumptions=compile_environment_assumptions(bindings={}),
    )
    active_graph = activate_compiled_world_graph(
        build_compiled_world_graph(store),
        environment=environment,
        solver=store.condition_solver(),
    )

    justifications = claim_justifications_from_active_graph(active_graph)
    by_id = {item.justification_id: item for item in justifications}

    assert by_id["reported:claim_a"].conclusion_claim_id == "claim_a"
    assert by_id["reported:claim_b"].premise_claim_ids == ()
    assert by_id["supports:claim_a->claim_b"].premise_claim_ids == ("claim_a",)
    assert by_id["supports:claim_a->claim_b"].conclusion_claim_id == "claim_b"
    assert by_id["explains:claim_b->claim_c"].premise_claim_ids == ("claim_b",)


def test_claim_justifications_from_active_graph_is_deterministic_under_relation_order_changes() -> (
    None
):
    store = _JustificationStore()
    reversed_store = _JustificationStore()
    reversed_store._claims = list(reversed(reversed_store._claims))
    reversed_store._stances = list(reversed(reversed_store._stances))
    environment = Environment(
        assumptions=compile_environment_assumptions(bindings={}),
    )

    forward = claim_justifications_from_active_graph(
        activate_compiled_world_graph(
            build_compiled_world_graph(store),
            environment=environment,
            solver=store.condition_solver(),
        )
    )
    reverse = claim_justifications_from_active_graph(
        activate_compiled_world_graph(
            build_compiled_world_graph(reversed_store),
            environment=environment,
            solver=reversed_store.condition_solver(),
        )
    )

    assert [item.to_dict() for item in forward] == [item.to_dict() for item in reverse]
