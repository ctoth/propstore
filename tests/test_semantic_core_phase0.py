from __future__ import annotations

import json

from propstore.world import BoundWorld, Environment, OverlayWorld, RenderPolicy, ResolutionStrategy, SyntheticClaim
from propstore.core.conditions import ConditionSolver
from propstore.core.labels import compile_environment_assumptions
from propstore.core.row_types import ConflictRowInput, StanceRowInput
from tests.atms_helpers import condition_registry_for_rows, rows_with_condition_ir


class _Store:
    def __init__(self) -> None:
        claims = [
            self._claim("claim_low", "concept1", value=10.0, sample_size=5),
            self._claim("claim_high", "concept1", value=20.0, sample_size=50),
            self._claim("claim_left", "concept2", value=5.0),
            self._claim("claim_right", "concept4", value=7.0),
        ]
        parameterizations = {
            "concept3": [
                {
                    "concept_ids": json.dumps(["concept2", "concept4"]),
                    "sympy": "Eq(concept3, concept2 + concept4)",
                    "formula": "concept3 = concept2 + concept4",
                    "exactness": "exact",
                    "conditions_cel": json.dumps(["x == 1", "y == 2"]),
                }
            ]
        }
        all_rows = claims + [
            row
            for rows in parameterizations.values()
            for row in rows
        ]
        self._condition_registry = condition_registry_for_rows(all_rows)
        self._claims = rows_with_condition_ir(claims, self._condition_registry)
        self._parameterizations = {
            concept_id: rows_with_condition_ir(rows, self._condition_registry)
            for concept_id, rows in parameterizations.items()
        }
        self._solver = ConditionSolver(self._condition_registry)

    @staticmethod
    def _claim(
        claim_id: str,
        concept_id: str,
        *,
        value: float,
        sample_size: int | None = None,
    ) -> dict:
        return {
            "id": claim_id,
            "concept_id": concept_id,
            "concept_links": [
                {
                    "claim_id": claim_id,
                    "concept_id": concept_id,
                    "role": "output",
                    "ordinal": 0,
                }
            ],
            "type": "parameter",
            "value": value,
            "sample_size": sample_size,
            "conditions_cel": json.dumps(["x == 1", "y == 2"]),
        }

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]

    def get_claim(self, claim_id: str) -> dict | None:
        return next((claim for claim in self._claims if claim["id"] == claim_id), None)

    def resolve_claim(self, claim_id: str) -> str | None:
        return claim_id if self.get_claim(claim_id) is not None else None

    def all_concepts(self) -> list[dict]:
        concept_ids = sorted({claim["concept_id"] for claim in self._claims} | {"concept3"})
        return [
            {"id": concept_id, "canonical_name": concept_id, "form": "structural"}
            for concept_id in concept_ids
        ]

    def get_concept(self, concept_id: str) -> dict | None:
        for concept in self.all_concepts():
            if concept["id"] == concept_id:
                return concept
        return None

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return list(self._parameterizations.get(concept_id, []))

    def condition_solver(self) -> ConditionSolver:
        return self._solver

    def conflicts(self) -> list[ConflictRowInput]:
        return []

    def explain(self, claim_id: str) -> list[StanceRowInput]:
        return []


def _make_bound(*, bindings: dict[str, object]) -> BoundWorld:
    environment = Environment(
        bindings=bindings,
        assumptions=compile_environment_assumptions(bindings=bindings),
    )
    return BoundWorld(
        _Store(),
        environment=environment,
        policy=RenderPolicy(strategy=ResolutionStrategy.SAMPLE_SIZE),
    )


def _runtime_claim_ids(claims) -> list[str]:
    return [str(claim.claim_id) for claim in claims]


def test_binding_order_does_not_change_active_or_resolved_semantics() -> None:
    forward = _make_bound(bindings={"x": 1, "y": 2})
    reverse = _make_bound(bindings={"y": 2, "x": 1})

    assert _runtime_claim_ids(forward.active_claims()) == _runtime_claim_ids(reverse.active_claims())

    forward_value = forward.value_of("concept1")
    reverse_value = reverse.value_of("concept1")
    assert forward_value.status == reverse_value.status == "conflicted"
    assert _runtime_claim_ids(forward_value.claims) == _runtime_claim_ids(reverse_value.claims)

    forward_derived = forward.derived_value("concept3")
    reverse_derived = reverse.derived_value("concept3")
    assert forward_derived.status == reverse_derived.status == "derived"
    assert forward_derived.value == reverse_derived.value == 12.0

    forward_resolved = forward.resolved_value("concept1")
    reverse_resolved = reverse.resolved_value("concept1")
    assert forward_resolved.status == reverse_resolved.status == "resolved"
    assert forward_resolved.winning_claim_id == reverse_resolved.winning_claim_id == "claim_high"
    assert forward_resolved.value == reverse_resolved.value == 20.0


def test_empty_hypothetical_overlay_is_identity_transform() -> None:
    bound = _make_bound(bindings={"x": 1, "y": 2})
    hypothetical = OverlayWorld(bound)

    assert _runtime_claim_ids(hypothetical.active_claims()) == _runtime_claim_ids(bound.active_claims())
    assert hypothetical.value_of("concept1") == bound.value_of("concept1")
    assert hypothetical.derived_value("concept3") == bound.derived_value("concept3")
    assert hypothetical.resolved_value("concept1") == bound.resolved_value("concept1")


def test_remove_and_add_inverse_overlay_returns_same_semantic_state() -> None:
    bound = _make_bound(bindings={"x": 1, "y": 2})
    inverse = OverlayWorld(
        bound,
        remove=["claim_left"],
        add=[
            SyntheticClaim(
                id="claim_left",
                concept_id="concept2",
                value=5.0,
                conditions=["x == 1", "y == 2"],
            )
        ],
    )

    assert _runtime_claim_ids(inverse.active_claims("concept2")) == ["claim_left"]
    assert inverse.value_of("concept2") == bound.value_of("concept2")
    assert inverse.derived_value("concept3") == bound.derived_value("concept3")
