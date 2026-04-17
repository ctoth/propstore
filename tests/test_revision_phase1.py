from __future__ import annotations

import json

from propstore.world import BoundWorld, Environment, ReasoningBackend, RenderPolicy
from propstore.core.row_types import ConflictRowInput, StanceRowInput
from tests.atms_helpers import _ExactMatchSolver, _OverlapSolver, leaf_lifting_system


class _RevisionStore:
    def __init__(self, *, claims: list[dict], solver=None) -> None:
        self._claims = list(claims)
        self._solver = solver or _ExactMatchSolver()

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim.get("concept_id") == concept_id]

    def get_claim(self, claim_id: str) -> dict | None:
        return next((claim for claim in self._claims if claim["id"] == claim_id), None)

    def all_parameterizations(self) -> list[dict]:
        return []

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        return []

    def conflicts(self) -> list[ConflictRowInput]:
        return []

    def all_concepts(self) -> list[dict]:
        concept_ids = sorted({claim["concept_id"] for claim in self._claims})
        return [{"id": concept_id, "canonical_name": concept_id} for concept_id in concept_ids]

    def explain(self, claim_id: str) -> list[StanceRowInput]:
        return []

    def condition_solver(self):
        return self._solver

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return []

    def resolve_concept(self, name: str) -> str | None:
        for claim in self._claims:
            if claim.get("concept_id") == name:
                return name
        return None

    def get_concept(self, concept_id: str) -> dict | None:
        return {"id": concept_id, "canonical_name": concept_id}


def _make_bound(
    store: _RevisionStore,
    *,
    bindings: dict[str, object] | None = None,
    context_id: str | None = None,
    effective_assumptions: tuple[str, ...] = (),
) -> BoundWorld:
    bindings = {} if bindings is None else bindings
    from propstore.core.labels import compile_environment_assumptions

    environment = Environment(
        bindings=bindings,
        context_id=context_id,
        effective_assumptions=effective_assumptions,
        assumptions=compile_environment_assumptions(
            bindings=bindings,
            effective_assumptions=effective_assumptions,
            context_id=context_id,
        ),
    )
    return BoundWorld(
        store,
        environment=environment,
        lifting_system=leaf_lifting_system(context_id) if context_id is not None else None,
        policy=RenderPolicy(reasoning_backend=ReasoningBackend.ATMS),
    )


def test_project_belief_base_includes_exact_support_claims_and_active_assumptions() -> None:
    from propstore.support_revision.projection import project_belief_base

    store = _RevisionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_semantic_only",
                "concept_id": "concept_semantic",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x > 0"]),
            },
        ],
        solver=_OverlapSolver(),
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = project_belief_base(bound)

    atom_ids = {atom.atom_id for atom in base.atoms}
    assumption_cels = {assumption.cel for assumption in base.assumptions}

    assert "claim:claim_exact" in atom_ids
    assert "claim:claim_semantic_only" not in atom_ids
    assert "x == 1" in assumption_cels


def test_compute_entrenchment_allows_explicit_overrides_to_outrank_default_support() -> None:
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.projection import project_belief_base

    store = _RevisionStore(
        claims=[
            {
                "id": "claim_unconditional",
                "concept_id": "concept_base",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": None,
            },
            {
                "id": "claim_override_target",
                "concept_id": "concept_focus",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    base = project_belief_base(bound)

    report = compute_entrenchment(
        bound,
        base,
        overrides={
            "claim:claim_override_target": {"priority": "critical"},
        },
    )

    assert report.ranked_atom_ids[0] == "claim:claim_override_target"
    assert report.reasons["claim:claim_override_target"].override_priority == "critical"


def test_bound_world_revision_phase1_delegates_to_revision_package() -> None:
    store = _RevisionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = bound.revision_base()
    entrenchment = bound.revision_entrenchment()

    assert hasattr(base, "atoms")
    assert hasattr(entrenchment, "ranked_atom_ids")
