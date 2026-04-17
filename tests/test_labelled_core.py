from __future__ import annotations

import json

from propstore.world.bound import BoundWorld
from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    JustificationRecord,
    Label,
    NogoodSet,
    combine_labels,
    compile_environment_assumptions,
    merge_labels,
)
from propstore.core.row_types import ConflictRowInput, StanceRowInput
from propstore.world.types import DerivedResult, Environment, ValueResult
from propstore.worldline import WorldlineDefinition, run_worldline

from tests.atms_helpers import _ExactMatchSolver, _OverlapSolver, leaf_lifting_system


class _StubStore:
    def __init__(self) -> None:
        self._claims = [
            {
                "id": "claim_x",
                "concept_id": "concept1",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_y",
                "concept_id": "concept2",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "claim_unconditional",
                "concept_id": "concept4",
                "type": "parameter",
                "value": 9.0,
                "conditions_cel": None,
            },
        ]

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [claim for claim in self._claims if claim["concept_id"] == concept_id]

    def parameterizations_for(self, concept_id: str) -> list[dict]:
        if concept_id != "concept3":
            return []
        return [{
            "concept_ids": json.dumps(["concept1", "concept2"]),
            "sympy": "Eq(concept3, concept1 + concept2)",
            "formula": "z = x + y",
            "exactness": "exact",
            "conditions_cel": None,
        }]

    def condition_solver(self) -> _ExactMatchSolver:
        return _ExactMatchSolver()

    def conflicts(self) -> list[ConflictRowInput]:
        return []

    def all_concepts(self) -> list[dict]:
        return []

    def explain(self, claim_id: str) -> list[StanceRowInput]:
        return []

    def get_claim(self, claim_id: str) -> dict | None:
        return next((claim for claim in self._claims if claim["id"] == claim_id), None)


def _make_bound(**bindings: object) -> BoundWorld:
    effective_assumptions = ("framework == 'general'",)
    environment = Environment(
        bindings=bindings,
        context_id="ctx_general",
        effective_assumptions=effective_assumptions,
        assumptions=compile_environment_assumptions(
            bindings=bindings,
            effective_assumptions=effective_assumptions,
            context_id="ctx_general",
        ),
    )
    return BoundWorld(_StubStore(), environment=environment)


def test_label_normalization_removes_duplicates() -> None:
    env = EnvironmentKey(("a",))

    label = Label((env, env))

    assert label.environments == (env,)


def test_label_normalization_prunes_supersets() -> None:
    subset = EnvironmentKey(("a",))
    superset = EnvironmentKey(("a", "b"))

    label = Label((superset, subset))

    assert label.environments == (subset,)


def test_nogoods_exclude_inconsistent_environments() -> None:
    nogoods = NogoodSet((EnvironmentKey(("a",)),))
    filtered = merge_labels(
        [
            Label(
                (
                    EnvironmentKey(("a",)),
                    EnvironmentKey(("a", "b")),
                    EnvironmentKey(("b",)),
                )
            )
        ],
        nogoods=nogoods,
    )

    assert filtered.environments == (EnvironmentKey(("b",)),)


def test_singleton_labels_use_compiled_assumption_identity() -> None:
    compiled = compile_environment_assumptions(
        bindings={"x": 1},
        effective_assumptions=("framework == 'general'",),
        context_id="ctx_general",
    )

    first = compile_environment_assumptions(
        bindings={"x": 1},
        effective_assumptions=("framework == 'general'",),
        context_id="ctx_general",
    )

    assert compiled == first
    assert compiled[0].assumption_id == first[0].assumption_id


def test_justification_combination_is_order_independent() -> None:
    compiled = compile_environment_assumptions(bindings={"x": 1, "y": 2})
    by_cel = {assumption.cel: assumption for assumption in compiled}

    left = JustificationRecord.from_antecedents(
        "concept3",
        (Label.singleton(by_cel["x == 1"]), Label.singleton(by_cel["y == 2"])),
    )
    right = JustificationRecord.from_antecedents(
        "concept3",
        (Label.singleton(by_cel["y == 2"]), Label.singleton(by_cel["x == 1"])),
    )

    assert left.label == right.label
    assert left.label.environments == (
        EnvironmentKey(
            (
                by_cel["x == 1"].assumption_id,
                by_cel["y == 2"].assumption_id,
            )
        ),
    )


def test_label_combination_is_associative_for_exact_support_products() -> None:
    assumption_a = AssumptionRef("a", "binding", "a", "a == 1")
    assumption_b = AssumptionRef("b", "binding", "b", "b == 2")
    assumption_c = AssumptionRef("c", "binding", "c", "c == 3")

    label_a = Label.singleton(assumption_a)
    label_b = Label.singleton(assumption_b)
    label_c = Label.singleton(assumption_c)

    left = combine_labels(combine_labels(label_a, label_b), label_c)
    right = combine_labels(label_a, combine_labels(label_b, label_c))

    assert left.environments == right.environments


def test_nogood_subsumption_prunes_non_minimal_inconsistent_environments() -> None:
    nogoods = NogoodSet(
        (
            EnvironmentKey(("a",)),
            EnvironmentKey(("a", "b")),
        )
    )

    filtered = merge_labels(
        [
            Label(
                (
                    EnvironmentKey(("a",)),
                    EnvironmentKey(("a", "b")),
                    EnvironmentKey(("b", "c")),
                )
            )
        ],
        nogoods=nogoods,
    )

    assert filtered.environments == (EnvironmentKey(("b", "c")),)


def test_unconditional_claim_gets_empty_environment_label() -> None:
    bound = _make_bound()

    result = bound.value_of("concept4")

    assert result.status == "determined"
    assert result.label == Label.empty()


def test_bound_world_uses_singleton_binding_labels() -> None:
    bound = _make_bound(x=1)
    by_cel = {assumption.cel: assumption for assumption in bound._environment.assumptions}

    result = bound.value_of("concept1")

    assert result.status == "determined"
    assert result.label == Label.singleton(by_cel["x == 1"])


def test_context_scoped_claim_is_not_labeled_as_unconditional() -> None:
    class ContextScopedStore(_StubStore):
        def __init__(self) -> None:
            self._claims = [
                {
                    "id": "claim_ctx",
                    "concept_id": "concept_ctx",
                    "type": "parameter",
                    "value": 7.0,
                    "conditions_cel": None,
                    "context_id": "ctx_general",
                }
            ]

    bound = BoundWorld(
        ContextScopedStore(),
        environment=Environment(
            context_id="ctx_general",
            effective_assumptions=("framework == 'general'",),
            assumptions=compile_environment_assumptions(
                bindings={},
                effective_assumptions=("framework == 'general'",),
                context_id="ctx_general",
            ),
        ),
        lifting_system=leaf_lifting_system("ctx"),
    )

    result = bound.value_of("concept_ctx")

    assert result.status == "determined"
    assert result.label is None


def test_semantically_active_claim_without_exact_assumption_match_gets_no_label() -> None:
    class SemanticOverlapStore(_StubStore):
        def __init__(self) -> None:
            self._claims = [
                {
                    "id": "claim_overlap",
                    "concept_id": "concept_overlap",
                    "type": "parameter",
                    "value": 11.0,
                    "conditions_cel": json.dumps(["x > 0"]),
                }
            ]

        def condition_solver(self) -> _OverlapSolver:
            return _OverlapSolver()

    bound = BoundWorld(
        SemanticOverlapStore(),
        environment=Environment(
            bindings={"x": 1},
            assumptions=compile_environment_assumptions(bindings={"x": 1}),
        ),
    )

    result = bound.value_of("concept_overlap")

    assert result.status == "determined"
    assert result.label is None


def test_derived_value_combines_input_labels() -> None:
    bound = _make_bound(x=1, y=2)
    by_cel = {assumption.cel: assumption for assumption in bound._environment.assumptions}

    result = bound.derived_value("concept3")

    assert result.status == "derived"
    assert result.value == 5.0
    assert result.label == Label(
        (
            EnvironmentKey(
                (
                    by_cel["x == 1"].assumption_id,
                    by_cel["y == 2"].assumption_id,
                )
            ),
        )
    )


def test_worldline_outputs_do_not_serialize_internal_labels() -> None:
    class FakeBound:
        def value_of(self, concept_id: str) -> ValueResult:
            return ValueResult(
                concept_id=concept_id,
                status="determined",
                claims=[{"id": "claim1", "value": 42.0}],
                label=Label.empty(),
            )

        def derived_value(
            self,
            concept_id: str,
            *,
            override_values: dict[str, float | str | None] | None = None,
        ) -> DerivedResult:
            return DerivedResult(concept_id=concept_id, status="no_relationship")

        def active_claims(self, concept_id: str | None = None) -> list[dict]:
            return [{"id": "claim1", "value": 42.0}]

    class FakeWorld:
        def bind(self, environment=None, *, policy=None, **conditions):
            return FakeBound()

        def resolve_concept(self, name: str) -> str | None:
            return "concept1" if name == "target" else None

        def get_concept(self, concept_id: str) -> dict | None:
            if concept_id == "concept1":
                return {"id": "concept1", "canonical_name": "target"}
            return None

        def get_claim(self, claim_id: str) -> dict | None:
            if claim_id == "claim1":
                return {"id": "claim1", "value": 42.0}
            return None

        def has_table(self, name: str) -> bool:
            return False

    result = run_worldline(
        WorldlineDefinition.from_dict({"id": "label_compat", "targets": ["target"]}),
        FakeWorld(),
    )

    assert result.values["target"].status == "determined"
    assert result.values["target"].value == 42.0
    assert "label" not in result.values["target"].to_dict()
